"""Capped proposed-GA runner for the interactive app demo."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from math import sqrt
from statistics import mean
from typing import Any

from truck_loading.packing import place_boxes_in_container, validate_placements


MM3_PER_LITER = 1_000_000.0
PACKING_STRATEGIES = (
    "volume_desc",
    "footprint_desc",
    "height_desc",
    "original_order",
)


PALETTE = (
    "#22d3c5",
    "#f7c948",
    "#ff6b5f",
    "#8aa0b4",
    "#7c3aed",
    "#16a34a",
    "#f97316",
    "#0ea5e9",
    "#ec4899",
    "#84cc16",
)


@dataclass(frozen=True)
class ProposedGAConfig:
    population_size: int = 40
    generations: int = 50
    seed: int = 42
    max_boxes_per_route: int = 500
    crossover_probability: float = 0.9
    mutation_probability: float = 0.22

    @classmethod
    def capped(cls, population_size: int | float, generations: int | float) -> "ProposedGAConfig":
        return cls(
            population_size=max(10, min(60, int(population_size))),
            generations=max(2, min(60, int(generations))),
        )


def run_proposed_ga(
    data: dict[str, Any],
    truck_dimensions_mm: tuple[float, float, float],
    config: ProposedGAConfig | None = None,
) -> dict[str, Any]:
    """Run a compact packing-aware GA and return route placements for the viewer."""
    config = config or ProposedGAConfig()
    rng = random.Random(config.seed)
    started = time.perf_counter()

    depot, customers = _split_depot_and_customers(data.get("customers", []))
    customer_ids = [customer["customer_id"] for customer in customers]
    customer_map = {customer["customer_id"]: customer for customer in customers}
    box_map = {str(box["box_id"]): box for box in data.get("boxes", [])}
    container = {
        "L": float(truck_dimensions_mm[0]),
        "W": float(truck_dimensions_mm[1]),
        "H": float(truck_dimensions_mm[2]),
    }

    if not customer_ids:
        raise ValueError("Proposed GA needs at least one real customer.")

    population = _initial_population(customer_ids, customer_map, rng, config.population_size)
    best_order: list[int] | None = None
    best_score = float("inf")
    best_info: dict[str, Any] | None = None
    history: list[float] = []

    for _generation in range(config.generations):
        scored = [
            (
                _score_order(order, depot, customer_map, box_map, container, config),
                order,
            )
            for order in population
        ]
        scored.sort(key=lambda item: item[0][0])
        score, info = scored[0][0]
        if score < best_score:
            best_score = score
            best_order = scored[0][1][:]
            best_info = info
        history.append(best_score)

        elite_count = max(2, int(round(config.population_size * 0.12)))
        next_population = [order[:] for _, order in scored[:elite_count]]
        while len(next_population) < config.population_size:
            parent_a = _tournament(scored, rng)
            parent_b = _tournament(scored, rng)
            if rng.random() < config.crossover_probability:
                child = _order_crossover(parent_a, parent_b, rng)
            else:
                child = parent_a[:]
            _mutate(child, rng, config.mutation_probability)
            next_population.append(child)
        population = next_population

    if best_order is None or best_info is None:
        best_order = customer_ids
        best_score, best_info = _score_order(best_order, depot, customer_map, box_map, container, config)

    best_score, best_info = _score_order(best_order, depot, customer_map, box_map, container, config)
    runtime = time.perf_counter() - started
    return {
        "model": "proposed_ga",
        "best_order": best_order,
        "best_score": best_score,
        "best_info": best_info,
        "history": history,
        "runtime_seconds": runtime,
        "config": {
            "population_size": config.population_size,
            "generations": config.generations,
            "max_boxes_per_route": config.max_boxes_per_route,
            "seed": config.seed,
        },
    }


def _split_depot_and_customers(customers: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    depot = next((customer for customer in customers if customer.get("is_depot")), customers[0] if customers else {})
    real_customers = [customer for customer in customers if not customer.get("is_depot")]
    normalized = []
    for customer in real_customers:
        customer_id = customer.get("customer_id", customer.get("id"))
        normalized.append({**customer, "customer_id": customer_id})
    return depot, normalized


def _initial_population(
    customer_ids: list[Any],
    customer_map: dict[Any, dict[str, Any]],
    rng: random.Random,
    population_size: int,
) -> list[list[int]]:
    population = [customer_ids[:], list(reversed(customer_ids))]
    by_angle = sorted(customer_ids, key=lambda cid: _angle_key(customer_map[cid]))
    population.append(by_angle)
    while len(population) < population_size:
        population.append(rng.sample(customer_ids, len(customer_ids)))
    return population[:population_size]


def _angle_key(customer: dict[str, Any]) -> float:
    return float(customer.get("x", 0)) * 10000.0 + float(customer.get("y", 0))


def _score_order(
    order: list[Any],
    depot: dict[str, Any],
    customer_map: dict[Any, dict[str, Any]],
    box_map: dict[str, dict[str, Any]],
    container: dict[str, float],
    config: ProposedGAConfig,
) -> tuple[float, dict[str, Any]]:
    routes = _decode_by_packability(order, customer_map, box_map, container, config.max_boxes_per_route)
    route_details = []
    total_distance = 0.0
    total_boxes = 0
    total_packed = 0
    feasible_routes = 0

    for route_index, route in enumerate(routes, start=1):
        detail = _evaluate_route(route_index, route, depot, customer_map, box_map, container)
        route_details.append(detail)
        total_distance += detail["distance"]
        total_boxes += detail["boxes_total"]
        total_packed += detail["boxes_packed"]
        feasible_routes += 1 if detail["feasible"] else 0

    route_count = len(route_details)
    infeasible_routes = route_count - feasible_routes
    unpacked_boxes = max(0, total_boxes - total_packed)
    fill_rates = [route["fill_rate"] for route in route_details] or [0.0]
    avg_fill = mean(fill_rates)
    min_fill = min(fill_rates)
    score = (
        total_distance
        + route_count * 150.0
        + infeasible_routes * 100000.0
        + unpacked_boxes * 1500.0
        + _fill_balance_penalty(fill_rates) * 900.0
        - avg_fill * 250.0
    )
    return score, {
        "total_distance": total_distance,
        "route_count": route_count,
        "infeasible_routes": infeasible_routes,
        "feasible_routes": feasible_routes,
        "boxes_total": total_boxes,
        "boxes_packed": total_packed,
        "unpacked_boxes": unpacked_boxes,
        "avg_fill_rate": avg_fill,
        "min_fill_rate": min_fill,
        "max_fill_rate": max(fill_rates),
        "routes": route_details,
    }


def _decode_by_box_count(order: list[Any], customer_box_count: dict[Any, int], max_boxes_per_route: int) -> list[list[Any]]:
    routes: list[list[Any]] = []
    current: list[Any] = []
    current_boxes = 0
    for customer_id in order:
        box_count = customer_box_count.get(customer_id, 0)
        if current and current_boxes + box_count > max_boxes_per_route:
            routes.append(current)
            current = []
            current_boxes = 0
        current.append(customer_id)
        current_boxes += box_count
    if current:
        routes.append(current)
    return routes


def _decode_by_packability(
    order: list[Any],
    customer_map: dict[Any, dict[str, Any]],
    box_map: dict[str, dict[str, Any]],
    container: dict[str, float],
    max_boxes_per_route: int,
) -> list[list[Any]]:
    routes: list[list[Any]] = []
    current: list[Any] = []
    current_boxes: list[dict[str, Any]] = []

    for customer_id in order:
        customer_boxes = _boxes_for_customers([customer_id], customer_map, box_map)
        candidate_boxes = current_boxes + customer_boxes
        exceeds_guard = len(candidate_boxes) > max_boxes_per_route
        candidate_result = _best_packing_result(container, candidate_boxes)
        candidate_fits = candidate_result["placed_count"] == len(candidate_boxes)

        if current and (exceeds_guard or not candidate_fits):
            routes.append(current)
            current = [customer_id]
            current_boxes = customer_boxes
            continue

        current.append(customer_id)
        current_boxes = candidate_boxes

    if current:
        routes.append(current)
    return routes


def _boxes_for_customers(
    route: list[Any],
    customer_map: dict[Any, dict[str, Any]],
    box_map: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    boxes = []
    for customer_id in route:
        customer = customer_map[customer_id]
        for box_id in customer.get("assigned_boxes", []):
            box = box_map.get(str(box_id))
            if box is not None:
                boxes.append(box)
    return boxes


def _ordered_boxes(strategy: str, boxes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if strategy == "volume_desc":
        return sorted(boxes, key=_box_volume, reverse=True)
    if strategy == "footprint_desc":
        return sorted(boxes, key=lambda box: float(box["length"]) * float(box["width"]), reverse=True)
    if strategy == "height_desc":
        return sorted(boxes, key=lambda box: float(box["height"]), reverse=True)
    return list(boxes)


def _best_packing_result(container: dict[str, float], boxes: list[dict[str, Any]]) -> dict[str, Any]:
    if not boxes:
        return {
            "placements": [],
            "packed_volume": 0.0,
            "placed_count": 0,
            "strategy": "original_order",
        }

    best: dict[str, Any] | None = None
    for strategy in PACKING_STRATEGIES:
        ordered = _ordered_boxes(strategy, boxes)
        placements, packed_volume, placed_count = place_boxes_in_container(container, ordered)
        candidate = {
            "placements": placements,
            "packed_volume": packed_volume,
            "placed_count": placed_count,
            "strategy": strategy,
        }
        if best is None or (placed_count, packed_volume) > (best["placed_count"], best["packed_volume"]):
            best = candidate
    return best or {
        "placements": [],
        "packed_volume": 0.0,
        "placed_count": 0,
        "strategy": "original_order",
    }


def _evaluate_route(
    route_index: int,
    route: list[Any],
    depot: dict[str, Any],
    customer_map: dict[Any, dict[str, Any]],
    box_map: dict[str, dict[str, Any]],
    container: dict[str, float],
) -> dict[str, Any]:
    box_to_customer: dict[str, dict[str, Any]] = {}
    for customer_id in route:
        customer = customer_map[customer_id]
        for box_id in customer.get("assigned_boxes", []):
            box_to_customer[str(box_id)] = customer

    boxes = _boxes_for_customers(route, customer_map, box_map)
    packing_result = _best_packing_result(container, boxes)
    placements = packing_result["placements"]
    packed_volume = packing_result["packed_volume"]
    packed_count = packing_result["placed_count"]
    validation_errors = validate_placements(placements, container)
    enriched = [
        _enrich_placement(route_index, placement, box_to_customer.get(str(placement["box_id"])))
        for placement in placements
    ]
    packed_ids = {str(placement["box_id"]) for placement in placements}
    all_ids = [str(box["box_id"]) for box in boxes]
    unpacked = [box_id for box_id in all_ids if box_id not in packed_ids]
    container_volume = container["L"] * container["W"] * container["H"]
    route_box_volume = sum(_box_volume(box) for box in boxes)
    distance = _route_distance(depot, customer_map, route)
    return {
        "route_index": route_index,
        "route": route,
        "customer_labels": [_customer_label(customer_map[customer_id]) for customer_id in route],
        "customer_count": len(route),
        "distance": distance,
        "feasible": packed_count == len(boxes) and not validation_errors,
        "boxes_total": len(boxes),
        "boxes_packed": packed_count,
        "unpacked_box_ids": unpacked,
        "fill_rate": packed_volume / container_volume if container_volume else 0.0,
        "packing_strategy": packing_result["strategy"],
        "truck_volume_liters": container_volume / MM3_PER_LITER,
        "route_box_volume_liters": route_box_volume / MM3_PER_LITER,
        "placements": enriched,
        "placement_errors": validation_errors,
    }


def _box_volume(box: dict[str, Any]) -> float:
    return float(box["length"]) * float(box["width"]) * float(box["height"])


def _enrich_placement(
    route_index: int,
    placement: dict[str, float | str],
    customer: dict[str, Any] | None,
) -> dict[str, Any]:
    customer_id = customer.get("customer_id", customer.get("id")) if customer else "unknown"
    customer_label = _customer_label(customer) if customer else "Unassigned customer"
    color = _customer_color(str(customer_id))
    return {
        **placement,
        "route_index": route_index,
        "customer_id": customer_id,
        "customer_label": customer_label,
        "color": color,
    }


def _customer_label(customer: dict[str, Any] | None) -> str:
    if not customer:
        return "Unknown customer"
    customer_id = customer.get("customer_id", customer.get("id", "unknown"))
    return str(customer.get("customer_name") or customer.get("name") or f"Customer {customer_id}")


def _customer_color(customer_id: str) -> str:
    try:
        index = int(customer_id)
    except ValueError:
        index = sum(ord(char) for char in customer_id)
    return PALETTE[index % len(PALETTE)]


def _route_distance(depot: dict[str, Any], customer_map: dict[Any, dict[str, Any]], route: list[Any]) -> float:
    if not route:
        return 0.0
    points = [_xy(depot)] + [_xy(customer_map[customer_id]) for customer_id in route] + [_xy(depot)]
    return sum(_distance(points[index], points[index + 1]) for index in range(len(points) - 1))


def _xy(customer: dict[str, Any]) -> tuple[float, float]:
    return (float(customer.get("x", 0.0)), float(customer.get("y", 0.0)))


def _distance(first: tuple[float, float], second: tuple[float, float]) -> float:
    return sqrt((first[0] - second[0]) ** 2 + (first[1] - second[1]) ** 2)


def _fill_balance_penalty(fill_rates: list[float]) -> float:
    if not fill_rates:
        return 0.0
    average = mean(fill_rates)
    return sum(abs(fill_rate - average) for fill_rate in fill_rates) / len(fill_rates)


def _tournament(scored: list[tuple[tuple[float, dict[str, Any]], list[Any]]], rng: random.Random, size: int = 3) -> list[Any]:
    contenders = rng.sample(scored, min(size, len(scored)))
    contenders.sort(key=lambda item: item[0][0])
    return contenders[0][1][:]


def _order_crossover(parent_a: list[Any], parent_b: list[Any], rng: random.Random) -> list[Any]:
    if len(parent_a) < 2:
        return parent_a[:]
    start, end = sorted(rng.sample(range(len(parent_a)), 2))
    child: list[int | None] = [None] * len(parent_a)
    child[start : end + 1] = parent_a[start : end + 1]
    fill = [customer_id for customer_id in parent_b if customer_id not in child]
    fill_index = 0
    for index, value in enumerate(child):
        if value is None:
            child[index] = fill[fill_index]
            fill_index += 1
    return list(child)


def _mutate(order: list[Any], rng: random.Random, probability: float) -> None:
    if len(order) < 2 or rng.random() >= probability:
        return
    if rng.random() < 0.5:
        first, second = rng.sample(range(len(order)), 2)
        order[first], order[second] = order[second], order[first]
    else:
        start, end = sorted(rng.sample(range(len(order)), 2))
        order[start : end + 1] = reversed(order[start : end + 1])

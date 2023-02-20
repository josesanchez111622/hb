import curses
import itertools
import logging

from typing import Dict, List, Tuple
from django.core.management.base import BaseCommand
from booking.models import (BathroomCoverage, HomeType,
                            PowerType, ProductCatalog, Relocation, TankType)
from booking.tests.factories import CustomerLeadFactory, ProductCriteriaFactory

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def verify_search_results(self):
        customer_lead = CustomerLeadFactory.create()

        # These conditions should return more than zero results
        non_zero_conditions = [{
            'tank_type': [TankType.Tankless.value],
            'home_type': [HomeType.SINGLE_FAMILY.value, HomeType.TOWNHOME.value, HomeType.CONDO.value],
            'power_type': [PowerType.GAS.value],
            'bathroom_coverages': [x[0] for x in BathroomCoverage.choices],
            'relocation': [Relocation.NONE.value],
        }, {
            'tank_type': [TankType.Tank.value],
            'home_type': [HomeType.SINGLE_FAMILY.value, HomeType.TOWNHOME.value, HomeType.CONDO.value],
            'power_type': [PowerType.GAS.value, PowerType.ELECTRIC.value],
            'bathroom_coverages': [BathroomCoverage.ONE.value, BathroomCoverage.TWO.value, BathroomCoverage.THREE.value],
            'relocation': [Relocation.NONE.value],
        }, {
            'tank_type': [TankType.Tank.value],
            'home_type': [HomeType.SINGLE_FAMILY.value, HomeType.TOWNHOME.value, HomeType.CONDO.value],
            'power_type': [PowerType.GAS.value, PowerType.ELECTRIC.value],
            'bathroom_coverages': [BathroomCoverage.FOURORMORE.value],
            'relocation': [Relocation.NONE.value],
        }]

        # These conditions should return zero results
        zero_conditions = [{
            'tank_type': [TankType.Tankless.value],
            'home_type': [x[0] for x in HomeType.choices],
            'power_type': [PowerType.ELECTRIC.value, PowerType.PROPANE.value],
            'bathroom_coverages': [x[0] for x in BathroomCoverage.choices],
            'relocation': [x[0] for x in Relocation.choices],
        }]

        criterion_choices = {
            'tank_type': TankType.choices,
            'home_type': HomeType.choices,
            'power_type': PowerType.choices,
            'bathroom_coverage': BathroomCoverage.choices,
            'relocation': Relocation.choices,
        }

        def convert_criteron_to_dict(distinct_criteria: Tuple[Tuple]) -> Dict:
            return [dict(zip(criterion_choices.keys(), z)) for z in [dict(y).keys() for y in [x for x in distinct_criteria]]]

        def conditions_met(condition: dict, test_condition: dict):
            criteria_list = list(itertools.product(*condition.values()))
            expanded_conditions = [
                dict(zip(criterion_choices.keys(), criterion)) for criterion in criteria_list]

            passing_conditions = []
            for expanded_condition in expanded_conditions:
                passing_conditions.append(
                    test_condition | expanded_condition == test_condition)
            return any(passing_conditions), len(expanded_conditions)

        def verify_sort_conditions(products: List[ProductCatalog], stdscr, sorted_by_popular_count, sorted_by_price_count):
            products_test_list = list(map(lambda x: x.is_popular, products))
            all_are_sorted_by_popular = all(
                products_test_list[k] >= products_test_list[k+1] for k in range(len(products_test_list) - 1))

            if all_are_sorted_by_popular:
                sorted_by_popular_count += 1
                stdscr.addstr(
                    0, 0, f'SORTED_BY_POPULAR condition is met: {sorted_by_popular_count}')
            else:
                stdscr.addstr(
                    1, 0, f'SORTED_BY_POPULAR condition is NOT met{products_test_list}\n')

            popular_products = list(
                itertools.compress(products, products_test_list))
            popular_products_test_list = list(
                map(lambda x: x.final_price(), popular_products))
            all_popular_sorted_by_price = all(
                popular_products_test_list[l] <= popular_products_test_list[l+1] for l in range(len(popular_products_test_list) - 1))

            not_popular_products = list(itertools.compress(
                products, [not p for p in products_test_list]))
            not_popular_products_test_list = list(
                map(lambda x: x.final_price(), not_popular_products))
            all_non_popular_sorted_by_price = all(
                not_popular_products_test_list[m] <= not_popular_products_test_list[m+1] for m in range(len(not_popular_products_test_list) - 1))

            if all_popular_sorted_by_price and all_non_popular_sorted_by_price:
                sorted_by_price_count += 1
                stdscr.addstr(
                    2, 0, f'SORTED_BY_PRICE condition is met:   {sorted_by_popular_count}')
            else:
                stdscr.addstr(
                    3, 0, f'SORTED_BY_PRICE condition is NOT met: {popular_products_test_list} {not_popular_products_test_list}')

            return sorted_by_popular_count, sorted_by_price_count

        def verify_conditions():
            stdscr = curses.initscr()
            curses.start_color()
            curses.use_default_colors()

            non_zero_condition_passed_count = [0] * len(non_zero_conditions)
            non_zero_condition_passed_max_list = [0] * len(non_zero_conditions)
            zero_condition_passed_count = [0] * len(zero_conditions)
            zero_condition_passed_max_list = [0] * len(zero_conditions)

            sorted_by_popular_count = 0
            sorted_by_price_count = 0

            distinct_criteria = list(itertools.product(TankType.choices, HomeType.choices,
                                                       PowerType.choices, BathroomCoverage.choices, Relocation.choices))

            for distinct_criterion in convert_criteron_to_dict(distinct_criteria):
                product_criteria = ProductCriteriaFactory.create(
                    **distinct_criterion)
                products = ProductCatalog.get_products_from_criteria(
                    product_criteria)

                if (len(products) > 0):
                    sorted_by_popular_count, sorted_by_price_count = verify_sort_conditions(
                        products, stdscr, sorted_by_popular_count, sorted_by_price_count)

                for i, non_zero_condition in enumerate(non_zero_conditions):
                    matched, condition_count = conditions_met(
                        non_zero_condition, distinct_criterion)
                    non_zero_condition_passed_max_list[i] = condition_count
                    if matched:
                        non_zero_condition_passed_count[i] += 1
                        stdscr.addstr(5, 0, 'NON_ZERO_condition is met')
                        for i, non_zero_condition in enumerate(non_zero_conditions):
                            output_string = f'Product Criteria #{i+1} {non_zero_condition_passed_count[i]} of {non_zero_condition_passed_max_list[i]}\n'
                            stdscr.addstr(5+2*i+1, 0, f'{non_zero_condition}')
                            stdscr.addstr(5+2*i+2, 0, output_string)
                        assert len(products) > 0

                for j, zero_condition in enumerate(zero_conditions):
                    matched, condition_count = conditions_met(
                        zero_condition, distinct_criterion)
                    zero_condition_passed_max_list[j] = condition_count

                    if matched:
                        stdscr.addstr(11+len(non_zero_conditions),
                                      0, 'ZERO_condition is met')
                        zero_condition_passed_count[j] += 1
                        for i, zero_condition in enumerate(zero_conditions):
                            stdscr.addstr(
                                3+2*i+9+len(non_zero_conditions), 0, f'{zero_condition}')
                            output_string = f'Product Criteria #{i+1} {zero_condition_passed_count[i]} of {zero_condition_passed_max_list[i]}\n'
                            stdscr.addstr(
                                3+2*i+10+len(non_zero_conditions), 0, output_string)
                        assert len(products) == 0

                stdscr.refresh()

            stdscr.getkey()
            curses.nocbreak()
            curses.echo()
            curses.endwin()

        verify_conditions()

    def handle(self, *args, **kwargs):
        self.verify_search_results()

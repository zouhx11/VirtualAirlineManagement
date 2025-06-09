import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from core.config_manager import ConfigManager


@dataclass
class ForecastResult:
    """Data class for forecast results."""
    period: str
    revenue: float
    costs: float
    profit: float
    confidence_interval: Tuple[float, float]
    scenario: str


@dataclass
class ScenarioParameters:
    """Data class for scenario parameters."""
    fuel_price_change: float = 0.0  # Percentage change
    demand_change: float = 0.0      # Percentage change
    competition_change: float = 0.0  # Percentage change
    economic_factor: float = 1.0     # Economic multiplier


class ForecastingEngine:
    """Advanced forecasting and optimization engine for airline operations."""
    
    def __init__(self, airline_id: int):
        self.airline_id = airline_id
        self.config_manager = ConfigManager()
        
        # Forecasting parameters
        self.base_growth_rate = 0.05  # 5% annual growth
        self.seasonality_factors = {
            1: 0.85, 2: 0.80, 3: 0.90, 4: 0.95, 5: 1.05, 6: 1.15,
            7: 1.20, 8: 1.15, 9: 1.05, 10: 1.00, 11: 0.90, 12: 0.95
        }
        
        # Load historical data
        self.historical_data = self.load_historical_data()
        
    def load_historical_data(self) -> pd.DataFrame:
        """Load historical financial and operational data."""
        try:
            db_path = self.config_manager.get_database_path('userdata')
            
            # Sample historical data - in real implementation, this would come from database
            dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='M')
            
            # Generate sample historical data with trend and seasonality
            base_revenue = 1000000
            data = []
            
            for i, date in enumerate(dates):
                month = date.month
                trend = 1 + (self.base_growth_rate * i / 12)
                seasonal = self.seasonality_factors[month]
                noise = np.random.normal(1, 0.1)
                
                revenue = base_revenue * trend * seasonal * noise
                costs = revenue * 0.75  # 75% cost ratio
                profit = revenue - costs
                
                # Load factor and passenger data
                load_factor = 75 + np.random.normal(0, 5)
                passengers = int(revenue / 250)  # Average revenue per passenger
                
                data.append({
                    'date': date,
                    'revenue': revenue,
                    'costs': costs,
                    'profit': profit,
                    'load_factor': max(50, min(95, load_factor)),
                    'passengers': passengers,
                    'fuel_cost': costs * 0.35,
                    'crew_cost': costs * 0.25,
                    'maintenance_cost': costs * 0.15,
                    'other_costs': costs * 0.25
                })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"Error loading historical data: {e}")
            return pd.DataFrame()
    
    def generate_revenue_forecast(self, months: int = 6, scenario: str = 'base') -> List[ForecastResult]:
        """Generate revenue forecast for specified number of months."""
        if self.historical_data.empty:
            return []
        
        # Get scenario parameters
        scenario_params = self.get_scenario_parameters(scenario)
        
        # Calculate base forecast using time series analysis
        last_date = self.historical_data['date'].max()
        last_revenue = self.historical_data['revenue'].iloc[-1]
        
        forecasts = []
        current_date = last_date
        
        for month in range(1, months + 1):
            current_date += timedelta(days=30)  # Approximate month
            
            # Apply trend
            trend_factor = 1 + (self.base_growth_rate * month / 12)
            
            # Apply seasonality
            seasonal_factor = self.seasonality_factors[current_date.month]
            
            # Apply scenario parameters
            demand_factor = 1 + scenario_params.demand_change
            economic_factor = scenario_params.economic_factor
            
            # Calculate forecast
            forecast_revenue = (last_revenue * trend_factor * 
                              seasonal_factor * demand_factor * economic_factor)
            
            # Calculate costs with fuel price impact
            fuel_factor = 1 + scenario_params.fuel_price_change
            base_costs = forecast_revenue * 0.75
            fuel_costs = base_costs * 0.35 * fuel_factor
            other_costs = base_costs * 0.65
            total_costs = fuel_costs + other_costs
            
            forecast_profit = forecast_revenue - total_costs
            
            # Calculate confidence interval (±15% for demo)
            confidence_range = forecast_profit * 0.15
            confidence_interval = (
                forecast_profit - confidence_range,
                forecast_profit + confidence_range
            )
            
            forecasts.append(ForecastResult(
                period=current_date.strftime("%Y-%m"),
                revenue=forecast_revenue,
                costs=total_costs,
                profit=forecast_profit,
                confidence_interval=confidence_interval,
                scenario=scenario
            ))
        
        return forecasts
    
    def generate_demand_forecast(self, route: str, months: int = 6) -> List[Dict]:
        """Generate passenger demand forecast for a specific route."""
        # Sample implementation - would use route-specific historical data
        base_demand = 1000  # Monthly passengers
        forecasts = []
        
        for month in range(1, months + 1):
            date = datetime.now() + timedelta(days=30 * month)
            seasonal_factor = self.seasonality_factors[date.month]
            trend_factor = 1 + (0.03 * month / 12)  # 3% annual growth
            
            forecast_demand = int(base_demand * seasonal_factor * trend_factor)
            
            forecasts.append({
                'period': date.strftime("%Y-%m"),
                'route': route,
                'passengers': forecast_demand,
                'load_factor': min(95, 70 + (forecast_demand / base_demand) * 10),
                'revenue_per_passenger': 250 + np.random.normal(0, 25)
            })
        
        return forecasts
    
    def optimize_route_pricing(self, route: str, current_price: float) -> Dict:
        """Optimize pricing for maximum profitability."""
        # Price elasticity model (simplified)
        elasticity = -1.2  # Typical airline price elasticity
        
        # Current demand at current price
        base_demand = 1000
        
        # Test different price points
        price_tests = np.linspace(current_price * 0.7, current_price * 1.3, 20)
        best_profit = 0
        optimal_price = current_price
        
        for test_price in price_tests:
            # Calculate demand response
            price_change = (test_price - current_price) / current_price
            demand_change = elasticity * price_change
            adjusted_demand = base_demand * (1 + demand_change)
            
            # Calculate revenue and profit
            revenue = test_price * max(0, adjusted_demand)
            costs = adjusted_demand * 150  # Cost per passenger
            profit = revenue - costs
            
            if profit > best_profit:
                best_profit = profit
                optimal_price = test_price
        
        return {
            'current_price': current_price,
            'optimal_price': optimal_price,
            'price_change': (optimal_price - current_price) / current_price,
            'expected_profit_increase': (best_profit - (current_price * base_demand - base_demand * 150)),
            'demand_impact': elasticity * ((optimal_price - current_price) / current_price)
        }
    
    def analyze_fleet_optimization(self) -> Dict:
        """Analyze fleet composition for optimization opportunities."""
        # Sample fleet data - would come from database
        fleet_data = [
            {'aircraft': 'A320neo', 'count': 5, 'utilization': 11.5, 'cost_per_hour': 2800},
            {'aircraft': 'B737 MAX', 'count': 3, 'utilization': 12.2, 'cost_per_hour': 2900},
            {'aircraft': 'A350-900', 'count': 2, 'utilization': 13.8, 'cost_per_hour': 4200}
        ]
        
        total_capacity = sum(ac['count'] * ac['utilization'] * 30 for ac in fleet_data)  # Monthly hours
        total_cost = sum(ac['count'] * ac['utilization'] * 30 * ac['cost_per_hour'] for ac in fleet_data)
        
        # Calculate efficiency metrics
        efficiency_metrics = []
        for aircraft in fleet_data:
            monthly_hours = aircraft['count'] * aircraft['utilization'] * 30
            monthly_cost = monthly_hours * aircraft['cost_per_hour']
            
            efficiency_metrics.append({
                'aircraft': aircraft['aircraft'],
                'utilization_rate': aircraft['utilization'] / 14.0,  # Max 14 hours/day
                'cost_efficiency': aircraft['cost_per_hour'],
                'monthly_contribution': monthly_hours / total_capacity,
                'optimization_score': (aircraft['utilization'] / 14.0) / (aircraft['cost_per_hour'] / 3000)
            })
        
        # Optimization recommendations
        recommendations = []
        for metric in efficiency_metrics:
            if metric['utilization_rate'] < 0.8:
                recommendations.append(f"Increase utilization of {metric['aircraft']} fleet")
            if metric['optimization_score'] < 0.8:
                recommendations.append(f"Consider replacing {metric['aircraft']} with more efficient aircraft")
        
        return {
            'current_efficiency': total_capacity / total_cost * 1000,  # Hours per $1000
            'fleet_metrics': efficiency_metrics,
            'recommendations': recommendations,
            'potential_savings': total_cost * 0.05  # Estimated 5% savings potential
        }
    
    def get_scenario_parameters(self, scenario: str) -> ScenarioParameters:
        """Get parameters for different scenarios."""
        scenarios = {
            'base': ScenarioParameters(),
            'optimistic': ScenarioParameters(
                fuel_price_change=-0.10,
                demand_change=0.15,
                economic_factor=1.1
            ),
            'pessimistic': ScenarioParameters(
                fuel_price_change=0.25,
                demand_change=-0.20,
                economic_factor=0.9
            ),
            'high_fuel': ScenarioParameters(
                fuel_price_change=0.30,
                demand_change=-0.05
            ),
            'recession': ScenarioParameters(
                demand_change=-0.25,
                economic_factor=0.85
            )
        }
        
        return scenarios.get(scenario, ScenarioParameters())
    
    def calculate_break_even_analysis(self, route: str) -> Dict:
        """Calculate break-even analysis for a route."""
        # Sample route data
        fixed_costs = 50000  # Monthly fixed costs
        variable_cost_per_passenger = 120
        average_fare = 280
        
        # Break-even calculations
        break_even_passengers = fixed_costs / (average_fare - variable_cost_per_passenger)
        break_even_load_factor = break_even_passengers / 3000  # Assuming 3000 monthly capacity
        
        return {
            'route': route,
            'fixed_costs': fixed_costs,
            'variable_cost_per_passenger': variable_cost_per_passenger,
            'average_fare': average_fare,
            'contribution_margin': average_fare - variable_cost_per_passenger,
            'break_even_passengers': break_even_passengers,
            'break_even_load_factor': min(100, break_even_load_factor * 100),
            'safety_margin': max(0, 75 - break_even_load_factor * 100)  # Assuming 75% current load factor
        }
    
    def generate_financial_kpis(self) -> Dict:
        """Generate key financial performance indicators."""
        if self.historical_data.empty:
            return {}
        
        latest_data = self.historical_data.tail(12)  # Last 12 months
        
        # Calculate KPIs
        total_revenue = latest_data['revenue'].sum()
        total_costs = latest_data['costs'].sum()
        total_profit = latest_data['profit'].sum()
        
        avg_load_factor = latest_data['load_factor'].mean()
        total_passengers = latest_data['passengers'].sum()
        
        # Revenue metrics
        rask = total_revenue / (total_passengers * 1000)  # Revenue per Available Seat-Km (simplified)
        cask = total_costs / (total_passengers * 1000)   # Cost per Available Seat-Km
        
        # Profitability metrics
        profit_margin = (total_profit / total_revenue) * 100
        roc = (total_profit / (total_revenue * 0.3)) * 100  # Return on Capital (simplified)
        
        # Growth metrics
        if len(self.historical_data) >= 24:
            current_year = latest_data['revenue'].sum()
            previous_year = self.historical_data.tail(24).head(12)['revenue'].sum()
            revenue_growth = ((current_year - previous_year) / previous_year) * 100
        else:
            revenue_growth = 0
        
        return {
            'total_revenue': total_revenue,
            'total_costs': total_costs,
            'net_profit': total_profit,
            'profit_margin': profit_margin,
            'load_factor': avg_load_factor,
            'rask': rask,
            'cask': cask,
            'revenue_growth': revenue_growth,
            'return_on_capital': roc,
            'passengers_ytd': total_passengers,
            'cost_breakdown': {
                'fuel': latest_data['fuel_cost'].sum(),
                'crew': latest_data['crew_cost'].sum(),
                'maintenance': latest_data['maintenance_cost'].sum(),
                'other': latest_data['other_costs'].sum()
            }
        }
    
    def run_monte_carlo_simulation(self, months: int = 12, simulations: int = 1000) -> Dict:
        """Run Monte Carlo simulation for risk analysis."""
        results = {
            'revenues': [],
            'profits': [],
            'load_factors': []
        }
        
        for _ in range(simulations):
            sim_revenue = 0
            sim_profit = 0
            sim_load_factors = []
            
            for month in range(months):
                # Random variations
                demand_variation = np.random.normal(1, 0.15)
                fuel_variation = np.random.normal(1, 0.20)
                competition_impact = np.random.normal(1, 0.10)
                
                # Base values
                base_monthly_revenue = 2000000
                monthly_revenue = base_monthly_revenue * demand_variation * competition_impact
                
                # Costs with fuel variation
                monthly_costs = monthly_revenue * 0.75 * fuel_variation
                monthly_profit = monthly_revenue - monthly_costs
                
                # Load factor
                load_factor = max(50, min(95, 75 * demand_variation))
                
                sim_revenue += monthly_revenue
                sim_profit += monthly_profit
                sim_load_factors.append(load_factor)
            
            results['revenues'].append(sim_revenue)
            results['profits'].append(sim_profit)
            results['load_factors'].append(np.mean(sim_load_factors))
        
        # Calculate statistics
        return {
            'revenue': {
                'mean': np.mean(results['revenues']),
                'std': np.std(results['revenues']),
                'percentile_5': np.percentile(results['revenues'], 5),
                'percentile_95': np.percentile(results['revenues'], 95)
            },
            'profit': {
                'mean': np.mean(results['profits']),
                'std': np.std(results['profits']),
                'percentile_5': np.percentile(results['profits'], 5),
                'percentile_95': np.percentile(results['profits'], 95),
                'probability_loss': sum(1 for p in results['profits'] if p < 0) / simulations
            },
            'load_factor': {
                'mean': np.mean(results['load_factors']),
                'std': np.std(results['load_factors']),
                'percentile_5': np.percentile(results['load_factors'], 5),
                'percentile_95': np.percentile(results['load_factors'], 95)
            }
        }
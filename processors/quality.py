"""
Data Quality Module

This module implements data quality assessment and scoring functionality
to evaluate the quality of scraped data.
"""

import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import logging
import statistics

from .base import BaseProcessor, ProcessingResult, QualityError


class QualityMetric(Enum):
    """Data quality metrics"""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    VALIDITY = "validity"
    TIMELINESS = "timeliness"
    UNIQUENESS = "uniqueness"


@dataclass
class QualityScore:
    """Quality score for a dataset"""
    
    overall_score: float
    metric_scores: Dict[QualityMetric, float]
    issues: List[str]
    recommendations: List[str]
    record_count: int
    field_count: int
    timestamp: datetime
    
    @property
    def grade(self) -> str:
        """Get quality grade"""
        if self.overall_score >= 90:
            return "A"
        elif self.overall_score >= 80:
            return "B"
        elif self.overall_score >= 70:
            return "C"
        elif self.overall_score >= 60:
            return "D"
        else:
            return "F"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'overall_score': self.overall_score,
            'grade': self.grade,
            'metric_scores': {metric.value: score for metric, score in self.metric_scores.items()},
            'issues': self.issues,
            'recommendations': self.recommendations,
            'record_count': self.record_count,
            'field_count': self.field_count,
            'timestamp': self.timestamp.isoformat()
        }


class DataQualityChecker(BaseProcessor):
    """Data quality checker with comprehensive quality metrics"""
    
    def __init__(self, quality_config: Optional[Dict[str, Any]] = None):
        """Initialize quality checker with configuration"""
        super().__init__("DataQualityChecker")
        self.config = quality_config or {}
        
        # Quality thresholds
        self.thresholds = self.config.get('thresholds', {
            'completeness': 0.8,
            'accuracy': 0.9,
            'consistency': 0.85,
            'validity': 0.9,
            'uniqueness': 0.95
        })
        
        # Field importance weights
        self.field_weights = self.config.get('field_weights', {})
        
        # Quality rules
        self.quality_rules = self.config.get('rules', {})
        
        # Last quality score
        self.last_quality_score = None
    
    async def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Assess data quality (returns original data unchanged)"""
        if not data:
            return data
        
        # Calculate quality score
        quality_score = await self._calculate_quality_score(data)
        self.last_quality_score = quality_score
        
        # Log quality assessment
        self.logger.info(f"Data quality assessment completed: {quality_score.overall_score:.1f}/100 ({quality_score.grade})")
        
        if quality_score.issues:
            self.logger.warning(f"Found {len(quality_score.issues)} quality issues")
        
        return data
    
    async def _calculate_quality_score(self, data: List[Dict[str, Any]]) -> QualityScore:
        """Calculate comprehensive quality score"""
        metric_scores = {}
        issues = []
        recommendations = []
        
        # Calculate individual metric scores
        metric_scores[QualityMetric.COMPLETENESS] = await self._calculate_completeness(data, issues, recommendations)
        metric_scores[QualityMetric.CONSISTENCY] = await self._calculate_consistency(data, issues, recommendations)
        metric_scores[QualityMetric.UNIQUENESS] = await self._calculate_uniqueness(data, issues, recommendations)
        metric_scores[QualityMetric.VALIDITY] = await self._calculate_validity(data, issues, recommendations)
        
        # Calculate overall score (weighted average)
        weights = self.config.get('metric_weights', {
            QualityMetric.COMPLETENESS: 0.3,
            QualityMetric.CONSISTENCY: 0.25,
            QualityMetric.UNIQUENESS: 0.2,
            QualityMetric.VALIDITY: 0.25
        })
        
        overall_score = sum(
            metric_scores[metric] * weights.get(metric, 0.25)
            for metric in metric_scores
        )
        
        return QualityScore(
            overall_score=overall_score,
            metric_scores=metric_scores,
            issues=issues,
            recommendations=recommendations,
            record_count=len(data),
            field_count=len(data[0]) if data else 0,
            timestamp=datetime.utcnow()
        )
    
    async def _calculate_completeness(self, data: List[Dict[str, Any]], 
                                     issues: List[str], recommendations: List[str]) -> float:
        """Calculate data completeness score"""
        if not data:
            return 0.0
        
        total_fields = 0
        filled_fields = 0
        empty_fields = 0
        
        # Field-specific completeness
        field_completeness = {}
        
        for record in data:
            for field_name, value in record.items():
                total_fields += 1
                
                if field_name not in field_completeness:
                    field_completeness[field_name] = {'filled': 0, 'empty': 0}
                
                if value is None or value == '' or value == []:
                    empty_fields += 1
                    field_completeness[field_name]['empty'] += 1
                else:
                    filled_fields += 1
                    field_completeness[field_name]['filled'] += 1
        
        # Calculate completeness score
        completeness_score = (filled_fields / total_fields) if total_fields > 0 else 0.0
        
        # Check for problematic fields
        for field_name, stats in field_completeness.items():
            field_empty_rate = stats['empty'] / (stats['filled'] + stats['empty'])
            
            if field_empty_rate > 0.5:  # More than 50% empty
                weight = self.field_weights.get(field_name, 1.0)
                if weight >= 0.8:  # Important field
                    issues.append(f"High empty rate ({field_empty_rate:.1%}) for important field '{field_name}'")
                    recommendations.append(f"Improve data collection for field '{field_name}'")
        
        return completeness_score
    
    async def _calculate_consistency(self, data: List[Dict[str, Any]], 
                                   issues: List[str], recommendations: List[str]) -> float:
        """Calculate data consistency score"""
        if not data:
            return 0.0
        
        consistency_scores = []
        
        # Check field consistency
        for field_name in data[0].keys():
            field_values = [record.get(field_name) for record in data if field_name in record]
            field_values = [v for v in field_values if v is not None and v != '']
            
            if len(field_values) < 2:
                consistency_scores.append(1.0)  # Not enough data to assess consistency
                continue
            
            # Data type consistency
            types = set(type(v).__name__ for v in field_values)
            type_consistency = 1.0 if len(types) == 1 else 0.5
            
            # Format consistency (for strings)
            format_consistency = 1.0
            if all(isinstance(v, str) for v in field_values):
                # Check string format consistency
                lengths = [len(v) for v in field_values]
                if len(set(lengths)) > 1:
                    length_std = statistics.stdev(lengths) if len(lengths) > 1 else 0
                    format_consistency = max(0.0, 1.0 - (length_std / max(lengths)))
                
                # Check case consistency
                cases = [v[0].isupper() if v else False for v in field_values if v]
                if cases:
                    case_consistency = 1.0 if all(cases) or not any(cases) else 0.5
                    format_consistency = (format_consistency + case_consistency) / 2
            
            field_consistency = (type_consistency + format_consistency) / 2
            consistency_scores.append(field_consistency)
            
            # Flag inconsistent fields
            if field_consistency < 0.7:
                issues.append(f"Inconsistent data in field '{field_name}' (score: {field_consistency:.2f})")
                recommendations.append(f"Standardize format for field '{field_name}'")
        
        # Calculate overall consistency score
        overall_consistency = statistics.mean(consistency_scores) if consistency_scores else 1.0
        
        return overall_consistency
    
    async def _calculate_uniqueness(self, data: List[Dict[str, Any]], 
                                   issues: List[str], recommendations: List[str]) -> float:
        """Calculate data uniqueness score"""
        if not data:
            return 0.0
        
        uniqueness_scores = []
        
        # Check for duplicate records
        record_signatures = []
        for record in data:
            # Create signature from key fields or all fields
            key_fields = self.config.get('key_fields', list(record.keys()))
            signature = tuple(str(record.get(field, '')) for field in key_fields)
            record_signatures.append(signature)
        
        # Calculate duplicate rate
        unique_signatures = set(record_signatures)
        duplicate_rate = 1.0 - (len(unique_signatures) / len(record_signatures))
        uniqueness_scores.append(1.0 - duplicate_rate)
        
        if duplicate_rate > 0.1:  # More than 10% duplicates
            issues.append(f"High duplicate rate: {duplicate_rate:.1%}")
            recommendations.append("Implement deduplication logic")
        
        # Check field uniqueness (for fields that should be unique)
        unique_fields = self.config.get('unique_fields', [])
        
        for field_name in unique_fields:
            if field_name in data[0]:
                field_values = [record.get(field_name) for record in data if field_name in record]
                field_values = [v for v in field_values if v is not None and v != '']
                
                if len(field_values) != len(set(field_values)):
                    field_duplicates = len(field_values) - len(set(field_values))
                    duplicate_rate = field_duplicates / len(field_values)
                    uniqueness_scores.append(1.0 - duplicate_rate)
                    
                    issues.append(f"Duplicate values in unique field '{field_name}': {field_duplicates} duplicates")
                    recommendations.append(f"Ensure uniqueness constraint for field '{field_name}'")
                else:
                    uniqueness_scores.append(1.0)
        
        # Calculate overall uniqueness score
        overall_uniqueness = statistics.mean(uniqueness_scores) if uniqueness_scores else 1.0
        
        return overall_uniqueness
    
    async def _calculate_validity(self, data: List[Dict[str, Any]], 
                                 issues: List[str], recommendations: List[str]) -> float:
        """Calculate data validity score"""
        if not data:
            return 0.0
        
        # Use validation rules if available
        if self.quality_rules.get('validation_rules'):
            from .validator import DataValidator, ValidationRule, ValidationType
            
            validation_rules = []
            for field_name, rules in self.quality_rules['validation_rules'].items():
                for rule_config in rules:
                    rule = ValidationRule(
                        field_name=field_name,
                        validation_type=ValidationType(rule_config['type']),
                        **{k: v for k, v in rule_config.items() if k != 'type'}
                    )
                    validation_rules.append(rule)
            
            validator = DataValidator(validation_rules)
            validated_data = await validator.process(data)
            
            # Calculate validity score based on validation results
            if hasattr(validator, 'last_validation_results'):
                validation_results = validator.last_validation_results
                valid_records = sum(1 for result in validation_results if result.is_valid)
                validity_score = valid_records / len(validation_results) if validation_results else 1.0
                
                # Add validation issues
                for result in validation_results:
                    if not result.is_valid:
                        issues.extend(result.errors)
                        recommendations.extend(["Review and fix validation errors"])
                
                return validity_score
        
        # Basic validity checks
        validity_scores = []
        
        for record in data:
            record_validity = 1.0
            field_issues = 0
            
            for field_name, value in record.items():
                # Check for obviously invalid values
                if value is not None:
                    # Check for negative values where inappropriate
                    if field_name.lower() in ['age', 'price', 'quantity', 'count'] and isinstance(value, (int, float)):
                        if value < 0:
                            field_issues += 1
                    
                    # Check for invalid email formats
                    if field_name.lower() == 'email' and isinstance(value, str):
                        import re
                        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                        if not re.match(email_pattern, value):
                            field_issues += 1
                    
                    # Check for invalid URLs
                    if field_name.lower() in ['url', 'website', 'link'] and isinstance(value, str):
                        if not (value.startswith(('http://', 'https://')) or value.startswith('www.')):
                            field_issues += 1
            
            # Calculate record validity
            if field_issues > 0:
                record_validity = max(0.0, 1.0 - (field_issues / len(record)))
            
            validity_scores.append(record_validity)
        
        # Calculate overall validity score
        overall_validity = statistics.mean(validity_scores) if validity_scores else 1.0
        
        return overall_validity
    
    def get_quality_report(self) -> Dict[str, Any]:
        """Get detailed quality report"""
        if not self.last_quality_score:
            return {'status': 'No quality assessment available'}
        
        report = {
            'quality_score': self.last_quality_score.to_dict(),
            'thresholds': self.thresholds,
            'assessment': {
                'overall_grade': self.last_quality_score.grade,
                'passes_threshold': self.last_quality_score.overall_score >= self.thresholds.get('completeness', 0.8),
                'critical_issues': [issue for issue in self.last_quality_score.issues if 'critical' in issue.lower()],
                'improvement_areas': self._identify_improvement_areas()
            }
        }
        
        return report
    
    def _identify_improvement_areas(self) -> List[str]:
        """Identify areas for improvement based on quality score"""
        improvements = []
        
        for metric, score in self.last_quality_score.metric_scores.items():
            threshold = self.thresholds.get(metric.value, 0.8)
            
            if score < threshold:
                metric_name = metric.value.replace('_', ' ').title()
                improvements.append(f"Improve {metric_name} (current: {score:.1%}, target: {threshold:.1%})")
        
        return sorted(improvements, key=lambda x: x.split('(')[0].strip())
    
    def set_threshold(self, metric: Union[QualityMetric, str], threshold: float):
        """Set quality threshold for a metric"""
        if isinstance(metric, str):
            metric = QualityMetric(metric.lower())
        
        if not isinstance(metric, QualityMetric):
            raise ValueError(f"Invalid metric: {metric}")
        
        if not 0 <= threshold <= 1:
            raise ValueError("Threshold must be between 0 and 1")
        
        self.thresholds[metric.value] = threshold
        self.logger.info(f"Set {metric.value} threshold to {threshold}")
    
    def get_quality_trends(self, historical_scores: List[QualityScore]) -> Dict[str, Any]:
        """Analyze quality trends over time"""
        if len(historical_scores) < 2:
            return {'status': 'Insufficient data for trend analysis'}
        
        # Calculate trends
        overall_trend = historical_scores[-1].overall_score - historical_scores[0].overall_score
        
        metric_trends = {}
        for metric in QualityMetric:
            if metric in historical_scores[-1].metric_scores and metric in historical_scores[0].metric_scores:
                trend = historical_scores[-1].metric_scores[metric] - historical_scores[0].metric_scores[metric]
                metric_trends[metric.value] = {
                    'change': trend,
                    'direction': 'improving' if trend > 0 else 'declining' if trend < 0 else 'stable'
                }
        
        return {
            'overall_trend': {
                'change': overall_trend,
                'direction': 'improving' if overall_trend > 0 else 'declining' if overall_trend < 0 else 'stable'
            },
            'metric_trends': metric_trends,
            'period': f"{len(historical_scores)} assessments"
        }


# Convenience functions
def create_quality_checker(thresholds: Optional[Dict[str, float]] = None,
                           field_weights: Optional[Dict[str, float]] = None) -> DataQualityChecker:
    """Create a data quality checker with custom thresholds"""
    config = {}
    
    if thresholds:
        config['thresholds'] = thresholds
    
    if field_weights:
        config['field_weights'] = field_weights
    
    return DataQualityChecker(config)


def create_standard_quality_checker() -> DataQualityChecker:
    """Create a standard data quality checker with default settings"""
    return DataQualityChecker({
        'thresholds': {
            'completeness': 0.8,
            'accuracy': 0.9,
            'consistency': 0.85,
            'validity': 0.9,
            'uniqueness': 0.95
        },
        'field_weights': {
            'id': 0.9,
            'name': 0.8,
            'email': 0.7,
            'phone': 0.6
        }
    })


def create_strict_quality_checker() -> DataQualityChecker:
    """Create a strict data quality checker with high standards"""
    return DataQualityChecker({
        'thresholds': {
            'completeness': 0.95,
            'accuracy': 0.98,
            'consistency': 0.95,
            'validity': 0.98,
            'uniqueness': 0.99
        }
    })


def create_lenient_quality_checker() -> DataQualityChecker:
    """Create a lenient data quality checker with relaxed standards"""
    return DataQualityChecker({
        'thresholds': {
            'completeness': 0.6,
            'accuracy': 0.7,
            'consistency': 0.7,
            'validity': 0.8,
            'uniqueness': 0.8
        }
    })


if __name__ == "__main__":
    # Test the quality checker
    logging.basicConfig(level=logging.INFO)
    
    # Create test data with quality issues
    test_data = [
        {'name': 'John Doe', 'email': 'john@example.com', 'age': 30},
        {'name': 'Jane Smith', 'email': 'jane@example.com', 'age': 25},
        {'name': '', 'email': 'invalid-email', 'age': -5},  # Quality issues
        {'name': 'Bob Johnson', 'email': 'bob@example.com', 'age': 35},
        {'name': 'John Doe', 'email': 'john@example.com', 'age': 30},  # Duplicate
    ]
    
    # Create and run quality checker
    checker = create_standard_quality_checker()
    processed_data = asyncio.run(checker.process(test_data))
    
    # Get quality report
    report = checker.get_quality_report()
    print(f"Quality Report: {report}")
    
    # Get last quality score
    if checker.last_quality_score:
        print(f"Quality Score: {checker.last_quality_score.to_dict()}")

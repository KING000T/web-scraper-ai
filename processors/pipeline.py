"""
Data Processing Pipeline Module

This module implements a complete data processing pipeline that chains
multiple processors together for comprehensive data processing.
"""

import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging

from .base import BaseProcessor, ProcessingResult, ProcessingStats
from .cleaner import DataCleaner
from .validator import DataValidator, ValidationResult
from .transformer import DataTransformer


class DataProcessingPipeline(BaseProcessor):
    """Complete data processing pipeline with multiple processors"""
    
    def __init__(self, processors: List[BaseProcessor] = None, name: str = "DataPipeline"):
        """Initialize processing pipeline with processors"""
        super().__init__(name)
        self.processors = processors or []
        self.pipeline_stats = ProcessingStats()
        self.last_results = []
        
        # Validate processors
        self._validate_processors()
    
    def _validate_processors(self):
        """Validate that all processors are BaseProcessor instances"""
        for i, processor in enumerate(self.processors):
            if not isinstance(processor, BaseProcessor):
                raise ValueError(f"Processor {i} is not a BaseProcessor instance: {type(processor)}")
    
    def add_processor(self, processor: BaseProcessor, position: Optional[int] = None):
        """Add a processor to the pipeline"""
        if not isinstance(processor, BaseProcessor):
            raise ValueError("Processor must be a BaseProcessor instance")
        
        if position is None:
            self.processors.append(processor)
        else:
            self.processors.insert(position, processor)
        
        self.logger.info(f"Added processor {processor.name} at position {position or len(self.processors) - 1}")
    
    def remove_processor(self, processor_name: str) -> bool:
        """Remove a processor by name"""
        for i, processor in enumerate(self.processors):
            if processor.name == processor_name:
                removed = self.processors.pop(i)
                self.logger.info(f"Removed processor {processor_name}")
                return True
        return False
    
    def get_processor(self, processor_name: str) -> Optional[BaseProcessor]:
        """Get a processor by name"""
        for processor in self.processors:
            if processor.name == processor_name:
                return processor
        return None
    
    async def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process data through all processors in the pipeline"""
        if not data:
            return []
        
        start_time = datetime.utcnow()
        original_data = data.copy()
        current_data = data
        processing_results = []
        
        self.logger.info(f"Starting pipeline processing with {len(self.processors)} processors")
        self.logger.info(f"Processing {len(current_data)} records")
        
        for i, processor in enumerate(self.processors):
            try:
                self.logger.info(f"Applying processor {i+1}/{len(self.processors)}: {processor.name}")
                
                # Process data through current processor
                processor_result = processor.process_with_stats(current_data)
                current_data = processor_result.data
                processing_results.append(processor_result)
                
                # Update pipeline stats
                self.pipeline_stats.update(processor_result)
                
                self.logger.info(
                    f"Processor {processor.name} completed: "
                    f"{len(current_data)} records, "
                    f"{processor_result.processing_time:.2f}s"
                )
                
                # Stop processing if no data left
                if not current_data:
                    self.logger.warning(f"No data remaining after processor {processor.name}")
                    break
                
            except Exception as e:
                self.logger.error(f"Error in processor {processor.name}: {str(e)}")
                # Continue with next processor if continue_on_error is True
                if not getattr(processor, 'continue_on_error', True):
                    break
        
        # Calculate total processing time
        total_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Create final result
        final_result = ProcessingResult(
            data=current_data,
            original_data=original_data,
            processing_time=total_time,
            processor_name=self.name,
            metadata={
                'pipeline_processors': len(self.processors),
                'processor_results': [result.get_summary() for result in processing_results],
                'pipeline_stats': self.pipeline_stats.to_dict()
            }
        )
        
        # Store results
        self.last_results = processing_results
        self.last_final_result = final_result
        
        self.logger.info(
            f"Pipeline completed: {len(current_data)} records processed, "
            f"total time: {total_time:.2f}s, "
            f"success rate: {self.pipeline_stats.success_rate:.1f}%"
        )
        
        return current_data
    
    def process_with_validation(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process data and return detailed validation results"""
        processed_data = asyncio.run(self.process(data))
        
        # Extract validation results if validator is present
        validation_results = []
        for result in self.last_results:
            if hasattr(result, 'validation_result') and result.validation_result:
                validation_results.append(result.validation_result)
        
        return {
            'processed_data': processed_data,
            'validation_results': validation_results,
            'processing_stats': self.pipeline_stats.to_dict(),
            'processor_summaries': [result.get_summary() for result in self.last_results]
        }
    
    def get_pipeline_summary(self) -> Dict[str, Any]:
        """Get comprehensive pipeline summary"""
        if not self.last_results:
            return {'status': 'No processing results available'}
        
        summary = {
            'pipeline_name': self.name,
            'total_processors': len(self.processors),
            'processor_names': [p.name for p in self.processors],
            'pipeline_stats': self.pipeline_stats.to_dict(),
            'processor_summaries': [result.get_summary() for result in self.last_results],
            'total_processing_time': sum(result.processing_time for result in self.last_results)
        }
        
        # Add validation summary if available
        validation_results = []
        for result in self.last_results:
            if hasattr(result, 'validation_result') and result.validation_result:
                validation_results.append(result.validation_result)
        
        if validation_results:
            validator = DataValidator([])
            summary['validation_summary'] = validator.get_validation_summary(validation_results)
        
        return summary
    
    def reset_stats(self):
        """Reset all statistics"""
        super().reset_stats()
        self.pipeline_stats = ProcessingStats()
        for processor in self.processors:
            processor.reset_stats()
    
    def clone(self) -> 'DataProcessingPipeline':
        """Create a clone of this pipeline"""
        cloned_pipeline = DataProcessingPipeline(
            processors=self.processors.copy(),
            name=f"{self.name}_clone"
        )
        return cloned_pipeline


class ProcessingPipelineBuilder:
    """Builder pattern for creating processing pipelines"""
    
    def __init__(self):
        self.processors = []
        self.pipeline_name = "CustomPipeline"
    
    def name(self, name: str) -> 'ProcessingPipelineBuilder':
        """Set pipeline name"""
        self.pipeline_name = name
        return self
    
    def add_cleaner(self, config: Optional[Dict[str, Any]] = None) -> 'ProcessingPipelineBuilder':
        """Add data cleaner to pipeline"""
        cleaner = DataCleaner(config)
        self.processors.append(cleaner)
        return self
    
    def add_validator(self, validation_rules: List = None) -> 'ProcessingPipelineBuilder':
        """Add data validator to pipeline"""
        validator = DataValidator(validation_rules)
        self.processors.append(validator)
        return self
    
    def add_transformer(self, transformations: List = None) -> 'ProcessingPipelineBuilder':
        """Add data transformer to pipeline"""
        transformer = DataTransformer(transformations)
        self.processors.append(transformer)
        return self
    
    def add_processor(self, processor: BaseProcessor) -> 'ProcessingPipelineBuilder':
        """Add custom processor to pipeline"""
        self.processors.append(processor)
        return self
    
    def build(self) -> DataProcessingPipeline:
        """Build the processing pipeline"""
        pipeline = DataProcessingPipeline(self.processors, self.pipeline_name)
        return pipeline


# Convenience functions for creating common pipelines
def create_standard_pipeline(cleaning_config: Optional[Dict[str, Any]] = None,
                           validation_rules: Optional[List] = None,
                           transformations: Optional[List] = None) -> DataProcessingPipeline:
    """Create a standard data processing pipeline"""
    builder = ProcessingPipelineBuilder().name("StandardPipeline")
    
    if cleaning_config:
        builder.add_cleaner(cleaning_config)
    
    if validation_rules:
        builder.add_validator(validation_rules)
    
    if transformations:
        builder.add_transformer(transformations)
    
    return builder.build()


def create_cleaning_only_pipeline(config: Optional[Dict[str, Any]] = None) -> DataProcessingPipeline:
    """Create a pipeline with only data cleaning"""
    return ProcessingPipelineBuilder().name("CleaningOnly").add_cleaner(config).build()


def create_validation_only_pipeline(validation_rules: List) -> DataProcessingPipeline:
    """Create a pipeline with only data validation"""
    return ProcessingPipelineBuilder().name("ValidationOnly").add_validator(validation_rules).build()


def create_transformation_only_pipeline(transformations: List) -> DataProcessingPipeline:
    """Create a pipeline with only data transformation"""
    return ProcessingPipelineBuilder().name("TransformationOnly").add_transformer(transformations).build()


# Example usage patterns
def example_usage():
    """Example usage patterns for processing pipelines"""
    
    # Pattern 1: Standard pipeline
    pipeline = create_standard_pipeline(
        cleaning_config={'remove_html': True, 'normalize_whitespace': True},
        validation_rules=[],
        transformations=[]
    )
    
    # Pattern 2: Custom pipeline with builder
    from processors.validator import required_field, email_field
    from processors.transformer import map_field, calculate_field
    
    pipeline = (ProcessingPipelineBuilder()
                .name("EmailProcessingPipeline")
                .add_cleaner({'remove_html': True})
                .add_validator([
                    required_field('name'),
                    email_field('email', required=True)
                ])
                .add_transformer([
                    map_field('status', 'status_normalized', 
                             {'active': True, 'inactive': False}),
                    calculate_field('full_name', '{first_name} {last_name}')
                ])
                .build())
    
    # Pattern 3: Dynamic pipeline
    pipeline = DataProcessingPipeline()
    pipeline.add_processor(DataCleaner({'remove_html': True}))
    pipeline.add_processor(DataValidator([required_field('name')]))
    
    return pipeline


if __name__ == "__main__":
    # Test the pipeline
    logging.basicConfig(level=logging.INFO)
    
    # Create test data
    test_data = [
        {'name': 'John Doe', 'email': 'john@example.com', 'age': '30'},
        {'name': 'Jane Smith', 'email': 'jane@example.com', 'age': '25'},
        {'name': '', 'email': 'invalid-email', 'age': '35'}
    ]
    
    # Create and run pipeline
    pipeline = create_standard_pipeline()
    processed_data = asyncio.run(pipeline.process(test_data))
    
    print(f"Processed {len(processed_data)} records")
    print(f"Pipeline summary: {pipeline.get_pipeline_summary()}")

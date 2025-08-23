import pandas as pd
import os
from flask import current_app
from datetime import datetime

def export_to_csv(dataframe, filename, include_headers=True):
    """
    Export dataframe to CSV file
    
    Args:
        dataframe: pandas DataFrame to export
        filename: name of the file
        include_headers: whether to include column headers
    
    Returns:
        Path to the exported CSV file
    """
    # Create exports directory if it doesn't exist
    export_dir = os.path.join(current_app.root_path, '..', 'exports')
    os.makedirs(export_dir, exist_ok=True)
    
    # Full path for the output file
    file_path = os.path.join(export_dir, filename)
    
    # Export to CSV
    dataframe.to_csv(
        file_path,
        index=False,
        header=include_headers
    )
    
    return file_path

def filter_data_by_campaign(dataframe, campaign):
    return dataframe[dataframe['Campaign'] == campaign]

def export_validated_disputes(dataframe):
    validated_disputes = dataframe[dataframe['Status'] == 'Validated']
    return export_to_csv(validated_disputes, 'validated_disputes.csv')
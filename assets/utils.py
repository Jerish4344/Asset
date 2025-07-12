import re
import ipaddress
import pandas as pd
from typing import Dict, List, Tuple, Union, Optional, Any
from django.utils import timezone
from datetime import datetime
import logging

# Configure logger
logger = logging.getLogger(__name__)


def validate_ip_address(ip_address: str) -> Tuple[bool, str]:
    """
    Validates an IP address.
    
    Args:
        ip_address (str): The IP address to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not ip_address or not isinstance(ip_address, str):
        return False, "IP address cannot be empty"
    
    ip_address = ip_address.strip()
    
    try:
        # Use ipaddress module for validation
        ipaddress.ip_address(ip_address)
        return True, ""
    except ValueError:
        return False, "Invalid IP address format. Use format: xxx.xxx.xxx.xxx"


def validate_mac_address(mac_address: str) -> Tuple[bool, str]:
    """
    Validates a MAC address.
    
    Args:
        mac_address (str): The MAC address to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not mac_address or not isinstance(mac_address, str):
        return False, "MAC address cannot be empty"
    
    mac_address = mac_address.strip()
    
    # Normalize MAC address format (remove separators and convert to lowercase)
    mac_address = re.sub(r'[^a-fA-F0-9]', '', mac_address).lower()
    
    # Check if it's a valid MAC address (12 hexadecimal characters)
    if len(mac_address) != 12 or not all(c in '0123456789abcdef' for c in mac_address):
        return False, "Invalid MAC address format. Should contain 12 hexadecimal digits."
    
    return True, ""


def format_mac_address(mac_address: str, separator: str = ':') -> str:
    """
    Formats a MAC address with the specified separator.
    
    Args:
        mac_address (str): The MAC address to format
        separator (str): The separator to use (default: ':')
        
    Returns:
        str: The formatted MAC address
    """
    # Remove any existing separators and convert to lowercase
    mac_address = re.sub(r'[^a-fA-F0-9]', '', mac_address).lower()
    
    # Insert separators
    formatted = ''
    for i in range(0, len(mac_address), 2):
        if i > 0:
            formatted += separator
        formatted += mac_address[i:i+2]
    
    return formatted


def parse_ram_specification(ram_spec: str) -> Dict[str, Any]:
    """
    Parses RAM specification from string.
    
    Args:
        ram_spec (str): The RAM specification string (e.g., "16GB", "8 GB DDR4")
        
    Returns:
        Dict[str, Any]: Dictionary with parsed RAM details
    """
    if not ram_spec or not isinstance(ram_spec, str):
        return {"size": None, "unit": None, "type": None, "original": str(ram_spec)}
    
    ram_spec = ram_spec.strip().upper()
    result = {"original": ram_spec}
    
    # Extract size and unit
    size_match = re.search(r'(\d+(?:\.\d+)?)\s*(GB|MB|TB)', ram_spec)
    if size_match:
        result["size"] = float(size_match.group(1))
        result["unit"] = size_match.group(2)
    else:
        # Try to find just numbers
        num_match = re.search(r'(\d+(?:\.\d+)?)', ram_spec)
        if num_match:
            result["size"] = float(num_match.group(1))
            # Assume GB if no unit specified
            result["unit"] = "GB"
        else:
            result["size"] = None
            result["unit"] = None
    
    # Extract RAM type
    type_match = re.search(r'(DDR\d+|SDRAM|RDRAM)', ram_spec)
    if type_match:
        result["type"] = type_match.group(1)
    else:
        result["type"] = None
    
    return result


def parse_processor_specification(processor_spec: str) -> Dict[str, Any]:
    """
    Parses processor specification from string.
    
    Args:
        processor_spec (str): The processor specification string
        
    Returns:
        Dict[str, Any]: Dictionary with parsed processor details
    """
    if not processor_spec or not isinstance(processor_spec, str):
        return {"brand": None, "model": None, "cores": None, "speed": None, "original": str(processor_spec)}
    
    processor_spec = processor_spec.strip()
    result = {"original": processor_spec}
    
    # Extract brand
    if re.search(r'intel|xeon|core\s*i\d', processor_spec, re.IGNORECASE):
        result["brand"] = "Intel"
    elif re.search(r'amd|ryzen|epyc|opteron', processor_spec, re.IGNORECASE):
        result["brand"] = "AMD"
    else:
        result["brand"] = None
    
    # Extract model
    model_patterns = [
        r'(core\s*i\d[\-\s]*\d+\w*)',  # Intel Core i5-9600K
        r'(xeon\s*\w+[\-\s]*\d+\w*)',  # Intel Xeon E5-2680
        r'(ryzen\s*\d+\s*\d+\w*)',     # AMD Ryzen 7 3700X
        r'(epyc\s*\d+\w*)',            # AMD EPYC 7742
    ]
    
    for pattern in model_patterns:
        model_match = re.search(pattern, processor_spec, re.IGNORECASE)
        if model_match:
            result["model"] = model_match.group(1)
            break
    else:
        result["model"] = None
    
    # Extract cores
    cores_match = re.search(r'(\d+)\s*cores?', processor_spec, re.IGNORECASE)
    if cores_match:
        result["cores"] = int(cores_match.group(1))
    else:
        result["cores"] = None
    
    # Extract speed
    speed_match = re.search(r'(\d+(?:\.\d+)?)\s*(GHz|MHz)', processor_spec, re.IGNORECASE)
    if speed_match:
        result["speed"] = float(speed_match.group(1))
        result["speed_unit"] = speed_match.group(2)
    else:
        result["speed"] = None
        result["speed_unit"] = None
    
    return result


def parse_harddisk_specification(harddisk_spec: str) -> Dict[str, Any]:
    """
    Parses hard disk specification from string.
    
    Args:
        harddisk_spec (str): The hard disk specification string
        
    Returns:
        Dict[str, Any]: Dictionary with parsed hard disk details
    """
    if not harddisk_spec or not isinstance(harddisk_spec, str):
        return {"size": None, "unit": None, "type": None, "original": str(harddisk_spec)}
    
    harddisk_spec = harddisk_spec.strip().upper()
    result = {"original": harddisk_spec}
    
    # Extract size and unit
    size_match = re.search(r'(\d+(?:\.\d+)?)\s*(TB|GB|MB)', harddisk_spec)
    if size_match:
        result["size"] = float(size_match.group(1))
        result["unit"] = size_match.group(2)
    else:
        # Try to find just numbers
        num_match = re.search(r'(\d+(?:\.\d+)?)', harddisk_spec)
        if num_match:
            result["size"] = float(num_match.group(1))
            # Assume GB if no unit specified
            result["unit"] = "GB"
        else:
            result["size"] = None
            result["unit"] = None
    
    # Extract disk type
    if re.search(r'SSD', harddisk_spec):
        result["type"] = "SSD"
    elif re.search(r'HDD|SATA|SCSI', harddisk_spec):
        result["type"] = "HDD"
    elif re.search(r'NVME', harddisk_spec):
        result["type"] = "NVME"
    else:
        result["type"] = None
    
    return result


def read_excel_file(file_path: str, sheet_name: Optional[Union[str, int]] = 0) -> pd.DataFrame:
    """
    Reads an Excel file and returns a pandas DataFrame.
    
    Args:
        file_path (str): Path to the Excel file
        sheet_name (Optional[Union[str, int]]): Name or index of the sheet to read
        
    Returns:
        pd.DataFrame: DataFrame containing the Excel data
    """
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        return df
    except Exception as e:
        logger.error(f"Error reading Excel file: {str(e)}")
        raise


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizes column names in a DataFrame (lowercase, replace spaces with underscores).
    
    Args:
        df (pd.DataFrame): DataFrame to normalize
        
    Returns:
        pd.DataFrame: DataFrame with normalized column names
    """
    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
    return df


def map_excel_columns(df: pd.DataFrame) -> Dict[str, str]:
    """
    Maps expected column names to actual column names in the DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame with the data
        
    Returns:
        Dict[str, str]: Mapping of expected column names to actual column names
    """
    # Define expected columns and their possible names in Excel files
    column_mappings = {
        'computer_name': ['computer_name', 'name', 'asset_name', 'hostname', 'server_name'],
        'server_make': ['server_make', 'make', 'asset_make', 'manufacturer', 'vendor'],
        'type': ['type', 'asset_type', 'server_type', 'device_type'],
        'ram': ['ram', 'memory', 'ram_size'],
        'processor': ['processor', 'cpu', 'processor_type', 'cpu_type'],
        'harddisk': ['harddisk', 'hdd', 'storage', 'disk', 'hard_disk', 'hard_drive'],
        'ip_address': ['ip_address', 'ip', 'ipaddress', 'ip_addr', 'ipv4_address'],
        'mac_id': ['mac_id', 'mac', 'macid', 'mac_address', 'physical_address']
    }
    
    # Find actual column names in the DataFrame
    actual_columns = {}
    for key, possible_names in column_mappings.items():
        for name in possible_names:
            if name in df.columns:
                actual_columns[key] = name
                break
    
    return actual_columns


def extract_asset_data(df: pd.DataFrame, column_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Extracts asset data from a DataFrame using the provided column mapping.
    
    Args:
        df (pd.DataFrame): DataFrame with the data
        column_mapping (Dict[str, str]): Mapping of expected column names to actual column names
        
    Returns:
        List[Dict[str, Any]]: List of dictionaries containing asset data
    """
    assets = []
    
    for _, row in df.iterrows():
        # Skip rows without a computer name
        if 'computer_name' not in column_mapping or pd.isna(row[column_mapping['computer_name']]):
            continue
        
        asset = {
            'asset_name': row[column_mapping['computer_name']] if 'computer_name' in column_mapping else None,
            'asset_make': row[column_mapping['server_make']] if 'server_make' in column_mapping and not pd.isna(row[column_mapping['server_make']]) else None,
            'asset_type': row[column_mapping['type']] if 'type' in column_mapping and not pd.isna(row[column_mapping['type']]) else None,
            'features': {},
            'network_addresses': []
        }
        
        # Extract features
        if 'ram' in column_mapping and not pd.isna(row[column_mapping['ram']]):
            asset['features']['RAM'] = parse_ram_specification(str(row[column_mapping['ram']]))
        
        if 'processor' in column_mapping and not pd.isna(row[column_mapping['processor']]):
            asset['features']['PROCESSOR'] = parse_processor_specification(str(row[column_mapping['processor']]))
        
        if 'harddisk' in column_mapping and not pd.isna(row[column_mapping['harddisk']]):
            asset['features']['HARDDISK'] = parse_harddisk_specification(str(row[column_mapping['harddisk']]))
        
        # Extract network addresses
        if 'ip_address' in column_mapping and not pd.isna(row[column_mapping['ip_address']]):
            ip_address = str(row[column_mapping['ip_address']]).strip()
            is_valid, _ = validate_ip_address(ip_address)
            if is_valid:
                asset['network_addresses'].append({
                    'address_type': 'IP_ADDRESS',
                    'address_value': ip_address
                })
        
        if 'mac_id' in column_mapping and not pd.isna(row[column_mapping['mac_id']]):
            mac_address = str(row[column_mapping['mac_id']]).strip()
            is_valid, _ = validate_mac_address(mac_address)
            if is_valid:
                formatted_mac = format_mac_address(mac_address)
                asset['network_addresses'].append({
                    'address_type': 'MAC_ID',
                    'address_value': formatted_mac
                })
        
        assets.append(asset)
    
    return assets


def get_asset_summary(assets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates a summary of the assets.
    
    Args:
        assets (List[Dict[str, Any]]): List of asset dictionaries
        
    Returns:
        Dict[str, Any]: Summary statistics about the assets
    """
    summary = {
        'total_assets': len(assets),
        'asset_types': {},
        'asset_makes': {},
        'ram_sizes': {},
        'processor_brands': {},
        'storage_types': {}
    }
    
    for asset in assets:
        # Count asset types
        asset_type = asset.get('asset_type')
        if asset_type:
            summary['asset_types'][asset_type] = summary['asset_types'].get(asset_type, 0) + 1
        
        # Count asset makes
        asset_make = asset.get('asset_make')
        if asset_make:
            summary['asset_makes'][asset_make] = summary['asset_makes'].get(asset_make, 0) + 1
        
        # Count RAM sizes
        if 'RAM' in asset.get('features', {}):
            ram_info = asset['features']['RAM']
            ram_size = f"{ram_info.get('size')} {ram_info.get('unit')}" if ram_info.get('size') else 'Unknown'
            summary['ram_sizes'][ram_size] = summary['ram_sizes'].get(ram_size, 0) + 1
        
        # Count processor brands
        if 'PROCESSOR' in asset.get('features', {}):
            proc_info = asset['features']['PROCESSOR']
            brand = proc_info.get('brand') or 'Unknown'
            summary['processor_brands'][brand] = summary['processor_brands'].get(brand, 0) + 1
        
        # Count storage types
        if 'HARDDISK' in asset.get('features', {}):
            disk_info = asset['features']['HARDDISK']
            disk_type = disk_info.get('type') or 'Unknown'
            summary['storage_types'][disk_type] = summary['storage_types'].get(disk_type, 0) + 1
    
    return summary


def validate_excel_data(assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validates the extracted asset data and returns a list of validation errors.
    
    Args:
        assets (List[Dict[str, Any]]): List of asset dictionaries
        
    Returns:
        List[Dict[str, Any]]: List of validation errors
    """
    errors = []
    
    for i, asset in enumerate(assets):
        asset_name = asset.get('asset_name') or f"Row {i+2}"  # +2 because Excel is 1-indexed and has header row
        
        # Validate required fields
        if not asset.get('asset_name'):
            errors.append({
                'row': i+2,
                'asset': asset_name,
                'field': 'asset_name',
                'error': 'Asset name is required'
            })
        
        # Validate network addresses
        for addr in asset.get('network_addresses', []):
            if addr['address_type'] == 'IP_ADDRESS':
                is_valid, error = validate_ip_address(addr['address_value'])
                if not is_valid:
                    errors.append({
                        'row': i+2,
                        'asset': asset_name,
                        'field': 'ip_address',
                        'error': error
                    })
            
            elif addr['address_type'] == 'MAC_ID':
                is_valid, error = validate_mac_address(addr['address_value'])
                if not is_valid:
                    errors.append({
                        'row': i+2,
                        'asset': asset_name,
                        'field': 'mac_id',
                        'error': error
                    })
    
    return errors


def process_excel_file(file_path: str, sheet_name: Optional[Union[str, int]] = 0) -> Dict[str, Any]:
    """
    Processes an Excel file and returns the extracted asset data.
    
    Args:
        file_path (str): Path to the Excel file
        sheet_name (Optional[Union[str, int]]): Name or index of the sheet to read
        
    Returns:
        Dict[str, Any]: Dictionary containing the processed data and metadata
    """
    try:
        # Read the Excel file
        df = read_excel_file(file_path, sheet_name)
        
        # Normalize column names
        df = normalize_column_names(df)
        
        # Map columns
        column_mapping = map_excel_columns(df)
        
        # Extract asset data
        assets = extract_asset_data(df, column_mapping)
        
        # Validate data
        validation_errors = validate_excel_data(assets)
        
        # Generate summary
        summary = get_asset_summary(assets)
        
        return {
            'success': True,
            'assets': assets,
            'summary': summary,
            'validation_errors': validation_errors,
            'column_mapping': column_mapping,
            'total_rows': len(df),
            'processed_rows': len(assets),
            'timestamp': timezone.now()
        }
    
    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': timezone.now()
        }

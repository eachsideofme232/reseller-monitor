"""
Seller labeling utilities for categorizing sellers based on rules.
"""
import re
import yaml
from typing import Dict, Literal, Optional


def load_rules(path: str = "config/seller_rules.yaml") -> dict:
    """
    Load seller categorization rules from YAML file.
    
    Args:
        path: Path to YAML file containing rules
        
    Returns:
        Dictionary with seller categorization rules
        
    Examples:
        >>> import os
        >>> # Create a temporary YAML file for testing
        >>> test_rules = '''official:
        ...   exact: ["올리브영"]
        ...   regex: ["^.+공식스토어$"]
        ... reseller:
        ...   regex: ["쿠팡"]
        ... suspect:
        ...   regex: ["병행"]'''
        >>> with open('test_rules.yaml', 'w') as f:
        ...     _ = f.write(test_rules)
        >>> rules = load_rules('test_rules.yaml')
        >>> 'official' in rules
        True
        >>> 'exact' in rules['official']
        True
        >>> os.remove('test_rules.yaml')
    """
    with open(path, 'r', encoding='utf-8') as f:
        rules = yaml.safe_load(f)
    return rules


def label_seller(mall_name: str, rules: dict) -> Literal["official", "reseller", "suspect"]:
    """
    Label a seller based on mall name and categorization rules.
    
    Args:
        mall_name: Name of the mall/seller
        rules: Dictionary containing categorization rules
        
    Returns:
        Category label: "official", "reseller", or "suspect"
        
    Examples:
        >>> rules = {
        ...     'official': {
        ...         'exact': ['올리브영', '아모레퍼시픽공식'],
        ...         'regex': ['^.+공식스토어$']
        ...     },
        ...     'reseller': {
        ...         'regex': ['쿠팡', 'G마켓']
        ...     },
        ...     'suspect': {
        ...         'regex': ['병행', '해외']
        ...     }
        ... }
        >>> label_seller('올리브영', rules)
        'official'
        >>> label_seller('네이처리퍼블릭공식스토어', rules)
        'official'
        >>> label_seller('쿠팡', rules)
        'reseller'
        >>> label_seller('병행수입상품', rules)
        'suspect'
        >>> label_seller('', rules)
        'suspect'
        >>> label_seller(None, rules)
        'suspect'
        >>> label_seller('일반상점', rules)
        'suspect'
    """
    # Handle None or empty mall_name
    if not mall_name:
        return "suspect"
    
    # Check official sellers first (highest priority)
    if 'official' in rules:
        # Check exact matches
        if 'exact' in rules['official'] and mall_name in rules['official']['exact']:
            return "official"
        
        # Check regex patterns
        if 'regex' in rules['official']:
            for pattern in rules['official']['regex']:
                if re.search(pattern, mall_name):
                    return "official"
    
    # Check reseller
    if 'reseller' in rules and 'regex' in rules['reseller']:
        for pattern in rules['reseller']['regex']:
            if re.search(pattern, mall_name):
                return "reseller"
    
    # Check suspect patterns
    if 'suspect' in rules and 'regex' in rules['suspect']:
        for pattern in rules['suspect']['regex']:
            if re.search(pattern, mall_name):
                return "suspect"
    
    # Default to suspect if no match
    return "suspect"


if __name__ == "__main__":
    import doctest
    doctest.testmod()
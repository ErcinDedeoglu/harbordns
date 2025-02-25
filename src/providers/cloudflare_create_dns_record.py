from typing import Optional, Dict, Any
import logging
from .cloudflare_client import CloudflareClient
from .cloudflare_zone import find_best_matching_zone

def create_dns_record(
    hostname: str,
    target: str,
    type: str,
    ttl: int,
    **kwargs: Any
) -> Optional[Dict[str, Any]]:
    zone_name, zone_id = find_best_matching_zone(hostname)
    
    if not zone_name or not zone_id:
        logging.error(f"Failed to find matching zone for {hostname}")
        return None
    
    try:
        logging.info(f"Creating {type} record for {hostname} in zone {zone_name}")
        client = CloudflareClient.get_instance()
        result = client.dns.records.create(
            zone_id=zone_id,
            name=hostname,
            type=type,
            content=target,
            ttl=ttl,
            proxied=kwargs.get('proxied', False)
        )
        
        logging.info(f"Successfully created DNS record for {hostname}")
        logging.debug(f"Created record: {result}")
        
        return result
        
    except Exception as e:
        logging.error(f"Failed to create DNS record for {hostname}: {str(e)}")
        return None
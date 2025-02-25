import logging
from .cloudflare_client import CloudflareClient

zones_table = []

def update_zones_table_if_empty():
    """
    Update the static in-memory zones table only if it's empty.
    """
    if not zones_table:
        update_zones_table()

def update_zones_table():
    """
    Fetch the latest zones from Cloudflare and update the static in-memory table.
    """
    try:
        client = CloudflareClient.get_instance()
        zones = client.zones.list()
        logging.debug(f"### Found zones: {zones}")
        zones_table.clear()
        zones_table.extend([
            {'name': getattr(zone, 'name', 'Unknown'), 'id': getattr(zone, 'id', 'Unknown')}
            for zone in zones
        ])
        logging.info("Zones table updated successfully.")
        for zone in zones_table:
            logging.info(f"Zone: {zone['name']} (ID: {zone['id']})")
    except Exception as e:
        logging.error(f"Failed to list zones: {str(e)}")

def find_best_matching_zone(hostname: str):
    try:
        zones = {zone['name']: zone['id'] for zone in zones_table}
        matching_zones = [zone_name for zone_name in zones if zone_name in hostname]
        if not matching_zones:
            # No matching zone found; update the zones table and try again
            update_zones_table_if_empty()
            zones = {zone['name']: zone['id'] for zone in zones_table}
            matching_zones = [zone_name for zone_name in zones if zone_name in hostname]
            if not matching_zones:
                # Still no matching zone after update
                return None, None
            best_match = max(matching_zones, key=len)
            zone_id = zones[best_match]
            return best_match, zone_id
        best_match = max(matching_zones, key=len)
        zone_id = zones[best_match]
        return best_match, zone_id
    except Exception as e:
        logging.error(f"Error finding matching zone for {hostname}: {str(e)}")
        return None, None

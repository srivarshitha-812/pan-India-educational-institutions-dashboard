import sys
sys.path.insert(0, '.')
from dashboard_server import registry

registry.load_all()
print(f"Datasets loaded: {len(registry.final_lists)}")
for k, v in sorted(registry.final_lists.items()):
    print(f"  {k:35s}: {v['total_records']:,} ({v['category']})")

summary = registry.get_summary()
kpis = summary['kpis']
print(f"\nKPIs:")
print(f"  Total records final: {kpis['total_records_final']:,}")
print(f"  States covered: {kpis['states_covered']}")
print(f"  Final lists count: {kpis['final_lists_count']}")

vci_list = registry.final_lists.get('vci_veterinary_colleges')
print(f"\nVCI Veterinary Colleges dataset in registry: {vci_list is not None}")
if vci_list:
    print(f"  Total records: {vci_list['total_records']}")
    print(f"  Category: {vci_list['category']}")
    print(f"  States covered: {vci_list['states_covered']}")
    print(f"  Official ID: {vci_list['official_id_col']}")

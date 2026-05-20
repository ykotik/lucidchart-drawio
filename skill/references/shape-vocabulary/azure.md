# Azure Shape Vocabulary (mxgraph.azure2.*)

draw.io ships Microsoft Azure icons under the `mxgraph.azure2.*` shape namespace.

## Base style scaffold

```
sketch=0;points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];outlineConnect=0;fontColor=#0072C6;gradientColor=none;fillColor=#0072C6;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.azure2.<SERVICE>;
```

Size: 60×60. Label below.

---

## Compute

| Service | shape= |
|---|---|
| Virtual Machine | `mxgraph.azure2.virtual_machine` |
| VM Scale Set | `mxgraph.azure2.vm_scale_set` |
| App Services | `mxgraph.azure2.app_services` |
| Function App | `mxgraph.azure2.function_apps` |
| Container Instances | `mxgraph.azure2.container_instances` |
| AKS / Kubernetes | `mxgraph.azure2.kubernetes_services` |
| Service Fabric | `mxgraph.azure2.service_fabric` |
| Batch | `mxgraph.azure2.batch_accounts` |
| Spring Apps | `mxgraph.azure2.spring_cloud` |
| Logic Apps | `mxgraph.azure2.logic_apps` |

---

## Storage

| Service | shape= |
|---|---|
| Storage Account | `mxgraph.azure2.storage_accounts` |
| Blob Storage | `mxgraph.azure2.blob_block` |
| Disk Storage | `mxgraph.azure2.disks` |
| Data Lake Storage | `mxgraph.azure2.data_lake_storage_gen1` |
| File Storage | `mxgraph.azure2.storage_accounts__classic_` |
| Queue Storage | `mxgraph.azure2.queue` |
| Table Storage | `mxgraph.azure2.table` |

---

## Database

| Service | shape= |
|---|---|
| SQL Database | `mxgraph.azure2.sql_database` |
| SQL Managed Instance | `mxgraph.azure2.sql_managed_instance` |
| SQL Server on VM | `mxgraph.azure2.sql_server_on_virtual_machines` |
| Cosmos DB | `mxgraph.azure2.cosmos_db` |
| PostgreSQL | `mxgraph.azure2.azure_database_postgresql_server` |
| MySQL | `mxgraph.azure2.azure_database_mysql_server` |
| MariaDB | `mxgraph.azure2.azure_database_mariadb_server` |
| Cache for Redis | `mxgraph.azure2.cache_redis` |
| Synapse Analytics | `mxgraph.azure2.synapse_analytics` |
| Data Factory | `mxgraph.azure2.data_factory` |

---

## Networking

| Service | shape= |
|---|---|
| Virtual Network | `mxgraph.azure2.virtual_networks` |
| Subnet | `mxgraph.azure2.subnet` |
| Load Balancer | `mxgraph.azure2.load_balancer` |
| Application Gateway | `mxgraph.azure2.application_gateway` |
| Front Door | `mxgraph.azure2.front_door_and_cdn_profiles` |
| Traffic Manager | `mxgraph.azure2.traffic_manager_profile` |
| DNS Zone | `mxgraph.azure2.dns_zones` |
| Network Security Group | `mxgraph.azure2.network_security_groups` |
| Private Link | `mxgraph.azure2.private_link` |
| VPN Gateway | `mxgraph.azure2.vpn_gateway` |
| ExpressRoute | `mxgraph.azure2.expressroute_circuits` |
| Bastion | `mxgraph.azure2.bastion` |
| Firewall | `mxgraph.azure2.firewalls` |
| CDN | `mxgraph.azure2.cdn_profile` |

---

## Identity & Security

| Service | shape= |
|---|---|
| Entra ID (Azure AD) | `mxgraph.azure2.azure_active_directory` |
| Entra ID B2C | `mxgraph.azure2.azure_ad_b2c` |
| Managed Identity | `mxgraph.azure2.managed_identities` |
| Key Vault | `mxgraph.azure2.key_vault` |
| Security Center | `mxgraph.azure2.security_center` |
| Sentinel | `mxgraph.azure2.azure_sentinel` |
| Defender for Cloud | `mxgraph.azure2.defender` |

---

## Integration

| Service | shape= |
|---|---|
| Service Bus | `mxgraph.azure2.service_bus` |
| Event Grid | `mxgraph.azure2.event_grid` |
| Event Hubs | `mxgraph.azure2.event_hubs` |
| Notification Hubs | `mxgraph.azure2.notification_hubs` |
| API Management | `mxgraph.azure2.api_management_services` |
| Logic Apps | `mxgraph.azure2.logic_apps` |

---

## DevOps / Monitoring

| Service | shape= |
|---|---|
| Application Insights | `mxgraph.azure2.application_insights` |
| Log Analytics | `mxgraph.azure2.log_analytics_workspaces` |
| Azure Monitor | `mxgraph.azure2.monitor` |
| DevOps Repos | `mxgraph.azure2.devops_repos` |
| DevOps Pipelines | `mxgraph.azure2.devops_pipelines` |
| Container Registry | `mxgraph.azure2.container_registries` |

---

## AI / ML

| Service | shape= |
|---|---|
| OpenAI Service | `mxgraph.azure2.openai_service` |
| Machine Learning | `mxgraph.azure2.machine_learning` |
| Cognitive Services | `mxgraph.azure2.cognitive_services` |
| AI Search | `mxgraph.azure2.cognitive_search` |
| Bot Service | `mxgraph.azure2.bot_services` |
| Form Recognizer | `mxgraph.azure2.form_recognizers` |

---

## Container groups (Azure scopes)

```
points=[...];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.azure2.virtual_networks;strokeColor=#0072C6;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#0072C6;dashed=1;
```

Use for `Subscription`, `Resource Group`, `Virtual Network`, `Subnet` containers. Set
`dashed=1` to differentiate cloud scopes from on-prem.

---

## Color palette

Primary Azure blue: `#0072C6`
Secondary teal: `#00BCF2`
Compute warm: `#E96424`
Identity green: `#7FBA00`
Security red: `#E81123`

Use the primary blue for most icons; switch the `fillColor` to the category color
when emphasizing the category boundary.

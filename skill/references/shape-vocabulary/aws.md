# AWS Shape Vocabulary (mxgraph.aws4.*)

draw.io ships AWS official icons under the `mxgraph.aws4.*` shape namespace. Use
these style strings as-is — do not invent variants.

All styles share a common scaffold; only the `shape=` value changes per service.

## Base style for any AWS service icon

```
sketch=0;points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#<TINT>;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.<SERVICE>;
```

Replace `<TINT>` and `<SERVICE>` per the tables below.

Sizes: square icons 78×78. Label appears below.

---

## Compute (orange #ED7100)

| Service | shape= |
|---|---|
| EC2 instance | `mxgraph.aws4.ec2` |
| EC2 (resource) | `mxgraph.aws4.ec2_instance` |
| Lambda | `mxgraph.aws4.lambda` |
| ECS / Container Service | `mxgraph.aws4.elastic_container_service` |
| EKS / Kubernetes | `mxgraph.aws4.elastic_kubernetes_service` |
| Fargate | `mxgraph.aws4.fargate` |
| Batch | `mxgraph.aws4.batch` |
| Auto Scaling | `mxgraph.aws4.ec2_auto_scaling` |
| Elastic Beanstalk | `mxgraph.aws4.elastic_beanstalk` |
| Lightsail | `mxgraph.aws4.lightsail` |
| App Runner | `mxgraph.aws4.app_runner` |

Tint: `ED7100`

---

## Storage (green #7AA116)

| Service | shape= |
|---|---|
| S3 bucket | `mxgraph.aws4.s3` |
| S3 Glacier | `mxgraph.aws4.s3_glacier` |
| EBS volume | `mxgraph.aws4.elastic_block_store` |
| EFS | `mxgraph.aws4.elastic_file_system` |
| FSx | `mxgraph.aws4.fsx` |
| Storage Gateway | `mxgraph.aws4.storage_gateway` |
| Backup | `mxgraph.aws4.backup` |

Tint: `7AA116`

---

## Database (blue #C925D1 — actually purple in AWS palette)

| Service | shape= |
|---|---|
| RDS | `mxgraph.aws4.rds` |
| Aurora | `mxgraph.aws4.aurora` |
| DynamoDB | `mxgraph.aws4.dynamodb` |
| ElastiCache | `mxgraph.aws4.elasticache` |
| Redshift | `mxgraph.aws4.redshift` |
| DocumentDB | `mxgraph.aws4.documentdb_with_mongodb_compatibility` |
| Neptune | `mxgraph.aws4.neptune` |
| Timestream | `mxgraph.aws4.timestream` |
| QLDB | `mxgraph.aws4.quantum_ledger_database_qldb` |
| Keyspaces | `mxgraph.aws4.keyspaces_for_apache_cassandra` |

Tint: `C925D1`

---

## Networking & Content Delivery (purple #8C4FFF)

| Service | shape= |
|---|---|
| VPC | `mxgraph.aws4.vpc` |
| Subnet | `mxgraph.aws4.vpc_subnet_public` / `mxgraph.aws4.vpc_subnet_private` |
| Internet Gateway | `mxgraph.aws4.internet_gateway` |
| NAT Gateway | `mxgraph.aws4.nat_gateway` |
| Route 53 | `mxgraph.aws4.route_53` |
| CloudFront | `mxgraph.aws4.cloudfront` |
| ELB (App LB) | `mxgraph.aws4.application_load_balancer` |
| ELB (Network LB) | `mxgraph.aws4.network_load_balancer` |
| API Gateway | `mxgraph.aws4.api_gateway` |
| Direct Connect | `mxgraph.aws4.direct_connect` |
| Transit Gateway | `mxgraph.aws4.transit_gateway` |
| VPN | `mxgraph.aws4.site_to_site_vpn` |
| Global Accelerator | `mxgraph.aws4.global_accelerator` |
| PrivateLink | `mxgraph.aws4.privatelink` |

Tint: `8C4FFF`

---

## Security, Identity & Compliance (red #DD344C)

| Service | shape= |
|---|---|
| IAM | `mxgraph.aws4.identity_and_access_management_iam` |
| IAM role | `mxgraph.aws4.role` |
| IAM user | `mxgraph.aws4.user` |
| Cognito | `mxgraph.aws4.cognito` |
| KMS | `mxgraph.aws4.key_management_service` |
| Secrets Manager | `mxgraph.aws4.secrets_manager` |
| GuardDuty | `mxgraph.aws4.guardduty` |
| Shield | `mxgraph.aws4.shield` |
| WAF | `mxgraph.aws4.waf` |
| Certificate Manager | `mxgraph.aws4.certificate_manager` |
| Macie | `mxgraph.aws4.macie` |
| Security Hub | `mxgraph.aws4.security_hub` |
| Inspector | `mxgraph.aws4.inspector` |

Tint: `DD344C`

---

## Application Integration (pink #E7157B)

| Service | shape= |
|---|---|
| SNS | `mxgraph.aws4.simple_notification_service` |
| SQS | `mxgraph.aws4.simple_queue_service` |
| EventBridge | `mxgraph.aws4.eventbridge` |
| Step Functions | `mxgraph.aws4.step_functions` |
| MQ | `mxgraph.aws4.mq` |
| AppSync | `mxgraph.aws4.appsync` |
| AppFlow | `mxgraph.aws4.appflow` |

Tint: `E7157B`

---

## Analytics (blue #8C4FFF / pink based)

| Service | shape= |
|---|---|
| Athena | `mxgraph.aws4.athena` |
| EMR | `mxgraph.aws4.emr` |
| Kinesis Data Streams | `mxgraph.aws4.kinesis_data_streams` |
| Kinesis Firehose | `mxgraph.aws4.kinesis_data_firehose` |
| Kinesis Analytics | `mxgraph.aws4.kinesis_data_analytics` |
| MSK (Managed Kafka) | `mxgraph.aws4.managed_streaming_for_apache_kafka` |
| Glue | `mxgraph.aws4.glue` |
| QuickSight | `mxgraph.aws4.quicksight` |
| Lake Formation | `mxgraph.aws4.lake_formation` |
| OpenSearch | `mxgraph.aws4.opensearch_service` |
| Data Pipeline | `mxgraph.aws4.data_pipeline` |

Tint: `8C4FFF`

---

## Management & Governance (red #E7157B / orange)

| Service | shape= |
|---|---|
| CloudWatch | `mxgraph.aws4.cloudwatch_2` |
| CloudFormation | `mxgraph.aws4.cloudformation` |
| CloudTrail | `mxgraph.aws4.cloudtrail` |
| Config | `mxgraph.aws4.config` |
| Systems Manager | `mxgraph.aws4.systems_manager` |
| Trusted Advisor | `mxgraph.aws4.trusted_advisor` |
| Organizations | `mxgraph.aws4.organizations` |
| Control Tower | `mxgraph.aws4.control_tower` |

Tint: `E7157B`

---

## ML / AI (turquoise #01A88D)

| Service | shape= |
|---|---|
| SageMaker | `mxgraph.aws4.sagemaker` |
| Bedrock | `mxgraph.aws4.bedrock` |
| Rekognition | `mxgraph.aws4.rekognition` |
| Comprehend | `mxgraph.aws4.comprehend` |
| Polly | `mxgraph.aws4.polly` |
| Translate | `mxgraph.aws4.translate` |
| Transcribe | `mxgraph.aws4.transcribe` |
| Textract | `mxgraph.aws4.textract` |
| Forecast | `mxgraph.aws4.forecast` |
| Personalize | `mxgraph.aws4.personalize` |
| Kendra | `mxgraph.aws4.kendra` |

Tint: `01A88D`

---

## Container groups

For VPC / subnet visual containers, use the AWS group shapes (transparent fill,
labeled at top-left):

```
points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_<TYPE>;strokeColor=#<STROKE>;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#<STROKE>;dashed=<DASHED>;
```

| Group type | grIcon | Stroke color | Dashed |
|---|---|---|---|
| AWS Cloud | `aws_cloud_alt` | `232F3E` | 0 |
| Region | `region` | `00A4A6` | 1 |
| VPC | `vpc` | `8C4FFF` | 0 |
| Availability Zone | `availability_zone` | `00A4A6` | 1 |
| Subnet (public) | `public_subnet` | `7AA116` | 0 |
| Subnet (private) | `private_subnet` | `00A4A6` | 0 |
| Auto Scaling group | `auto_scaling_group` | `ED7100` | 1 |
| Security group | `security_group` | `DD344C` | 0 |
| Account | `account` | `CD2264` | 1 |

---

## Common combinations (good defaults)

| Use case | Service icons in this order |
|---|---|
| Three-tier web app | Route 53 → CloudFront → ALB → EC2 → RDS |
| Serverless web | Route 53 → CloudFront → API Gateway → Lambda → DynamoDB |
| Event-driven | API Gateway → Lambda → SNS / EventBridge → SQS → Lambda |
| Streaming | Kinesis Data Streams → Kinesis Analytics → S3 + Redshift |
| ML pipeline | S3 → Glue → SageMaker → S3 (model) → Lambda (inference) |
| Container | ALB → ECS Fargate → RDS (with VPC + subnets) |

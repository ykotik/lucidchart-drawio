# ERD Crow's Foot – SaaS Multi-Tenant Data Model

Create an entity-relationship diagram using crow's foot notation for a SaaS multi-tenant platform.

## Entities

1. **Organization** – id, name, slug, created_at
2. **Workspace** – id, name, description, organization_id
3. **Project** – id, name, status, workspace_id
4. **Member** – id, user_id, workspace_id, joined_at
5. **User** – id, email, display_name, avatar_url, password_hash
6. **Task** – id, title, description, status, priority, project_id, assignee_id
7. **Document** – id, title, content, project_id, author_id
8. **Tag** – id, name, color
9. **Comment** – id, body, task_id, author_id, created_at
10. **Role** – id, name, permissions
11. **BillingAccount** – id, organization_id, payment_method, billing_email
12. **Subscription** – id, billing_account_id, plan, status, start_date, end_date
13. **Invoice** – id, subscription_id, amount, currency, issued_at, paid_at
14. **AuditLog** – id, organization_id, actor_id, action, resource_type, resource_id, timestamp

## Relationships

- Organization 1──┤< Workspace (one-to-many)
- Workspace 1──┤< Project (one-to-many)
- Workspace 1──┤< Member (one-to-many)
- Project 1──┤< Task (one-to-many)
- Project 1──┤< Document (one-to-many)
- Task >┤──┤< Tag (many-to-many, via TaskTag join)
- Task 1──┤< Comment (one-to-many)
- Member >┤──┤< Role (many-to-many, via MemberRole join)
- User 1──┤< Member (one-to-many)
- BillingAccount 1──1 Organization (one-to-one)
- BillingAccount 1──┤< Subscription (one-to-many)
- Subscription 1──┤< Invoice (one-to-many)
- Organization 1──┤< AuditLog (one-to-many)
- User 1──┤< AuditLog (one-to-many)
- User 1──┤< Comment (one-to-many)
- User 1──┤< Document (one-to-many)
- Member 1──┤< Task (one-to-many, as assignee)
- TaskTag – join table linking Task and Tag
- MemberRole – join table linking Member and Role

Layout the entities clearly with billing-related entities grouped together, workspace/project entities grouped together, and user/member entities grouped together.

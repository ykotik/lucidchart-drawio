# text-overflow

Build a scope-columns diagram for an identity and access management system.

Shapes to include:
- "Microsoft Azure Active Directory B2C" (external IdP, vendor scope)
- "Okta Workforce Identity Cloud" (internal IdP, internal scope)
- "SAP S/4HANA" with sub-label "[ERP Core] — Finance, HR, Procurement" (internal scope)
- "AWS Cognito User Pools" (cloud zone)
- "Legacy On-Premise LDAP Directory Server" (vendor scope, to be decommissioned)

Include edges:
- Azure AD B2C → Okta (SAML 2.0 federation)
- Okta → SAP S/4HANA (SCIM provisioning)
- Okta → AWS Cognito (JWT delegation)

Use the scope-columns pattern. All labels must fit inside their node boxes without overflow.

**Evaluation focus:** This case tests that the LLM runs `scripts/text-metrics.js` at Step 1.5
and applies `text_safe.min_width` / `text_safe.min_height` as geometry lower bounds before
emitting XML. The reference diagram uses correctly sized nodes. Validator must report
zero W106/W107/W108 violations.

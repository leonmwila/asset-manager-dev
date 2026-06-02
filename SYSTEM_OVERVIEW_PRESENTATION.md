# Asset Manager System Overview

## Slide 1: Title
- Asset Manager System Overview
- Odoo 19 Based Multi-Institution Asset Tracking Platform
- Prepared for stakeholders and operations teams

## Slide 2: Executive Summary
- The system centralizes asset and serial number lifecycle management.
- It supports institution-aware numbering, assignment, transfer, and disposal workflows.
- It runs on Docker with production deployment on a shared-IP server using Nginx and SSL.
- It includes custom modules tailored for operational, compliance, and reporting needs.

## Slide 3: Business Problem Solved
- Asset records were fragmented and difficult to reconcile across institutions.
- Bulk serial onboarding was slow and error-prone.
- Institution ownership and movement approvals were hard to enforce consistently.
- Reporting and traceability requirements needed stronger system controls.

## Slide 4: Solution Architecture
- Platform: Odoo 19 with PostgreSQL.
- Runtime: Docker Compose services for Odoo and database.
- Deployment mode: Shared IP with Nginx reverse proxy and Let's Encrypt TLS.
- Extensibility: Modular custom addons in a dedicated custom_addons layer.

## Slide 5: Core Functional Scope
- Bulk creation of Lot/Serial records with GRZ Number B auto-assignment.
- Institution-aware serial range enforcement.
- Asset labeling and barcode-related workflows.
- Inter-institution transfer requests and approvals.
- Asset disposal and donation processes.
- Depreciation and product-to-asset mapping enhancements.

## Slide 6: Key Custom Modules
- add_new_bulk_lots_serials: Bulk onboarding with serial and GRZ logic.
- company_extension: Institution, terminology, and business-rule extensions.
- institution_institution_transfer: Controlled transfer request workflow.
- asset_disposal: Disposal and donation transaction management.
- product_depreciation: Status and depreciation related controls.
- stock_allocation_from_none: Batch allocation of orphan serials to stock locations.

## Slide 7: Recent Enhancements Delivered
- Fixed GRZ Number B range selection to respect active institution context.
- Added optional stock location during bulk serial creation to avoid None location outcomes.
- Added Stock Allocation from None module for legacy orphan serial cleanup.
- Introduced background allocation jobs to keep UI responsive for large batches.
- Added completion popups with succeeded, failed, and skipped counters.

## Slide 8: End-to-End User Workflow
- User imports or creates serials in bulk.
- System assigns GRZ Number B from institution-specific available range.
- User allocates serials directly to stock location or queues allocation jobs.
- Users can initiate institution transfer requests where stock exists.
- Lifecycle events continue through assignment, reporting, and disposal.

## Slide 9: Security and Access Model
- Standard Odoo role and ACL model controls wizard and job access.
- Allocation targets are restricted to internal stock locations.
- Company compatibility checks prevent invalid cross-institution placement.
- Reverse proxy and SSL secure transport for production access.

## Slide 10: Performance and Scalability
- Background job queue prevents UI lock during high-volume allocations.
- Cron-driven processing supports concurrent user submissions.
- Conflict-safe behavior skips serials already stocked.
- Suitable for multi-user operations across institutions.

## Slide 11: Deployment and Operations
- Source-controlled in GitHub for traceability and repeatable deployments.
- Dockerized stack simplifies environment setup and updates.
- Shared-IP deployment integrates with existing Nginx domain routing.
- Automated certificate renewal handled by Certbot.

## Slide 12: Risks and Mitigations
- Risk: DNS or reverse proxy misconfiguration.
- Mitigation: Standardized Nginx templates and SSL verification checks.
- Risk: User role misconfiguration for background job operations.
- Mitigation: Controlled ACL updates and module-level upgrades.
- Risk: Legacy orphan serials from historical imports.
- Mitigation: Dedicated allocation wizard and background queue processing.

## Slide 13: Roadmap
- Add import template assistant for faster 500 to 1000 serial onboardings.
- Add richer job monitoring dashboard with filtering and retry actions.
- Add operational KPIs for allocation throughput and transfer aging.
- Add scheduled data quality checks for orphan and inconsistent records.

## Slide 14: Success Metrics
- Reduced time to onboard serials in bulk.
- Reduced manual correction effort for None-location records.
- Higher transfer traceability across institutions.
- Improved user experience under heavy operational loads.

## Slide 15: Closing
- The platform is operational, secure, and tailored to institutional asset workflows.
- Recent enhancements directly improved accuracy, speed, and scalability.
- Next phase can focus on analytics, automation, and governance reporting.

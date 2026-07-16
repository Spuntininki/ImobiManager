"""Contract PDF generation — formatters, renderer, and template data.

This subpackage houses the pipeline that turns a Contract (plus its owner,
renter, address, and documents) into a rendered PDF document:

1. ``formatters`` — pure functions that translate ORM model objects into the
   human-readable pt-BR strings the contract template expects.
2. ``renderer`` — turns a ``converted_data`` dict (sectioned lines) into PDF
   bytes, styled by a ``style_config`` dict.
3. ``validation`` — guards against template/formatter drift at load time.
4. ``_seed_data`` — the default contract template + style, sourced from
   ``contract_templates`` via the migration seeded from this module.

The orchestrator living one level up (``app.services.contract_pdf_service``)
composes these pieces against an injected ``AsyncSession``.
"""

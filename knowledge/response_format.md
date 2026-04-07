# Response Format Component Schemas

All responses must be valid JSON: `{"text": "...", "components": [...]}`.

## stat_card — Single metric display

```json
{"type": "stat_card", "label": "GRNs Today", "value": 5, "description": "Completed GRN transactions"}
```

## table — Data table with rows

```json
{"type": "table", "title": "Today's GRNs", "columns": ["ID", "Reference", "Status", "Items", "Created"], "rows": [["uuid...", "REF-001", "COMPLETED", 3, "2024-01-15T10:30:00"]]}
```

## bar_chart — Bar chart

```json
{"type": "bar_chart", "title": "GRNs by Status", "data": [{"name": "COMPLETED", "value": 5}, {"name": "PENDING", "value": 2}], "x_key": "name", "y_key": "value"}
```

## pie_chart — Pie/donut chart

```json
{"type": "pie_chart", "title": "Inventory by Zone", "data": [{"name": "Zone A", "value": 150}, {"name": "Zone B", "value": 80}]}
```

## line_chart — Line/trend chart

```json
{"type": "line_chart", "title": "Daily GRNs (Last 7 Days)", "data": [{"date": "Mon", "count": 3}, {"date": "Tue", "count": 5}], "x_key": "date", "y_key": "count"}
```

## detail_card — Key-value detail view for a single record

```json
{"type": "detail_card", "title": "Transaction Details", "fields": [{"label": "ID", "value": "uuid..."}, {"label": "Type", "value": "GRN"}, {"label": "Status", "value": "COMPLETED"}]}
```

## confirmation_dialog — Require user confirmation before executing a mutation

```json
{"type": "confirmation_dialog", "title": "Create GRN", "description": "Receive 100 units of SKU-A into PRE_PUTAWAY zone", "action": "wms_create_grn", "parameters": {}, "requires_confirmation": true}
```

## form — Dynamic form for collecting missing inputs before a tool call

```json
{"type": "form", "title": "Create GRN", "fields": [{"name": "sku_code", "label": "SKU Code", "type": "text", "required": true}, {"name": "quantity", "label": "Quantity", "type": "number", "required": true}], "action": "wms_create_grn"}
```

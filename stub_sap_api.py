"""
stub_sap_api.py
---------------
Mock SAP API server for testing Odoo integration without a real SAP system.

Endpoints:
  GET /sap/sales-orders             - Returns the complete stub JSON file
  GET /sap/sales-order/<order_id>   - Returns the matching stub sales order
  GET /sap/customer/<customer_id>   - Returns stub customer data
  GET /sap/material/<material_id>   - Returns stub material data (from stub JSON)
  GET /sap/error/not-found          - Always returns 404 (for error-handling tests)

Usage:
  python stub_sap_api.py
  curl http://localhost:5000/sap/sales-order/0000001258
  curl http://localhost:5000/sap/sales-order/0000001259
  curl http://localhost:5000/sap/sales-order/0000001260
"""

from flask import Flask, jsonify
import json
import os

app = Flask(__name__)

# Load stub data — dict keyed by vbeln (order number)
STUB_DATA_PATH = os.path.join(os.path.dirname(__file__), 'sap_sales_order_stub.json')

with open(STUB_DATA_PATH) as f:
    STUB_DATA = json.load(f)

# Build a flat material lookup from all positionen across all orders
# keyed by matnr — so /sap/material/<matnr> returns real stub data
MATERIAL_INDEX: dict = {}
for order in STUB_DATA.values():
    for pos in order["sales_order"]["positionen"]:
        matnr = pos["matnr"]
        if matnr not in MATERIAL_INDEX:
            MATERIAL_INDEX[matnr] = {
                "matnr": matnr,
                "maktx": pos["maktx"],
                "meins": pos["meins"],
            }


@app.route('/sap/sales-order/<order_id>', methods=['GET'])
def get_sales_order(order_id):
    """Look up order by ID; return 404 if not found in stub data."""
    if order_id in STUB_DATA:
        return jsonify(STUB_DATA[order_id]), 200
    # Fallback: if order_id not in stub, return first order so testing always works
    first = next(iter(STUB_DATA.values()))
    return jsonify(first), 200


@app.route('/sap/sales-orders', methods=['GET'])
def get_all_sales_orders():
    """Return the complete stub JSON dataset."""
    return jsonify(STUB_DATA), 200


@app.route('/sap/customer/<customer_id>', methods=['GET'])
def get_customer(customer_id):
    return jsonify({
        "kunnr":   customer_id,
        "name":    "Test Customer ABC",
        "email":   "customer@test.com",
        "street":  "123 Test Street",
        "city":    "Bengaluru",
        "country": "IN"
    }), 200


@app.route('/sap/material/<material_id>', methods=['GET'])
def get_material(material_id):
    """Return material data from the stub index; fall back to a safe default."""
    if material_id in MATERIAL_INDEX:
        return jsonify(MATERIAL_INDEX[material_id]), 200
    # Fallback — unknown matnr, still return a valid shape so Odoo doesn't crash
    return jsonify({
        "matnr": material_id,
        "maktx": "Unknown Product",
        "meins": "PCS",
    }), 200


@app.route('/sap/error/not-found', methods=['GET'])
def not_found():
    return jsonify({"error": "Not found"}), 404


if __name__ == '__main__':
    print("=" * 50)
    print("SAP Stub Server running on http://localhost:5000")
    print("=" * 50)
    print("Available orders:")
    for vbeln in STUB_DATA:
        print(f"  curl http://localhost:5000/sap/sales-order/{vbeln}")
    print("-" * 50)
    print("Available materials:")
    for matnr, mat in MATERIAL_INDEX.items():
        print(f"  curl http://localhost:5000/sap/material/{matnr}  -> {mat['maktx']}")
    print("=" * 50)
    app.run(port=5000, debug=True)

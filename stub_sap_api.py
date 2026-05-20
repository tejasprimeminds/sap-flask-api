"""
stub_sap_api.py
---------------
Mock SAP API server for testing Odoo integration without a real SAP system.

Endpoints:
  GET /sap/sales-orders             - Returns the complete stub JSON file
  GET /sap/sales-order/<order_id>   - Returns the matching stub sales order
  GET /sap/customer/<customer_id>   - Returns stub customer data
  GET /sap/material/<material_name> - Returns stub material data (keyed by maktx)
  GET /sap/error/not-found          - Always returns 404 (for error-handling tests)

Usage:
  python stub_sap_api.py
  curl http://localhost:5000/sap/sales-order/0000001258
  curl "http://localhost:5000/sap/material/AC"
  curl "http://localhost:5000/sap/material/Installation%20Service"
"""

from flask import Flask, jsonify
import json
import os

app = Flask(__name__)

# Load stub data — dict keyed by vbeln (order number)
STUB_DATA_PATH = os.path.join(os.path.dirname(__file__), 'sap_sales_order_stub.json')

with open(STUB_DATA_PATH) as f:
    STUB_DATA = json.load(f)

# Build a flat material lookup keyed by maktx (no matnr in JSON)
# e.g. MATERIAL_INDEX["AC"] = {"maktx": "AC", "meins": "PCS"}
MATERIAL_INDEX: dict = {}
for order in STUB_DATA.values():
    for pos in order["sales_order"]["positionen"]:
        maktx = pos["maktx"]
        if maktx not in MATERIAL_INDEX:
            MATERIAL_INDEX[maktx] = {
                "maktx": maktx,
                "meins": pos["meins"],
            }


@app.route('/sap/sales-order/<order_id>', methods=['GET'])
def get_sales_order(order_id):
    """Look up order by ID; fallback to first order if not found."""
    if order_id in STUB_DATA:
        return jsonify(STUB_DATA[order_id]), 200
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


@app.route('/sap/material/<path:material_name>', methods=['GET'])
def get_material(material_name):
    """
    Return material data keyed by maktx (product display name).
    Using <path:...> so names with spaces work after URL-decoding.
    e.g. /sap/material/Installation Service
    """
    if material_name in MATERIAL_INDEX:
        return jsonify(MATERIAL_INDEX[material_name]), 200
    # Fallback — unknown name, return a safe default shape
    return jsonify({
        "maktx": material_name,
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
    for maktx, mat in MATERIAL_INDEX.items():
        print(f"  curl 'http://localhost:5000/sap/material/{maktx}'  -> {mat['meins']}")
    print("=" * 50)
    app.run(port=5000, debug=True)

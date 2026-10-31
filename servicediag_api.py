"""Flask routes for ServiceDiag-AI.

These routes do not use private reference labels.
"""
from flask import Blueprint, jsonify, request
from servicediag_core import InputError, OutputError, assess_case, validate_case

servicediag_bp = Blueprint('servicediag', __name__)

@servicediag_bp.get('/api/servicediag/health')
def health():
    return jsonify({
        'status': 'ready',
        'engine': 'ServiceDiag-AI',
        'version': '1.0',
        'conditions': ['C1', 'C2'],
    })

@servicediag_bp.post('/api/servicediag/assess')
def assess():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or set(data) != {'condition', 'case'}:
        return jsonify({'error': 'Send JSON containing exactly condition and case.'}), 400
    try:
        condition, case = data['condition'], data['case']
        validate_case(case, condition)
        result = assess_case(case, condition)
        return jsonify(result)
    except (InputError, OutputError) as exc:
        return jsonify({'error_type': type(exc).__name__, 'error': str(exc)}), 422
    except Exception as exc:
        # Keep internal error details out of the response.
        return jsonify({
            'error_type': type(exc).__name__,
            'error': 'Diagnostic call failed; inspect local service configuration.',
        }), 503

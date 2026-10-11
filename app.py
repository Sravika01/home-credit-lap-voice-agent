import os
from flask import Flask, render_template_string, request

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Home Credit | LAP Eligibility Demo</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f3f6fb;
            margin: 0;
            padding: 30px 16px;
            color: #1f2937;
        }
        .container {
            max-width: 760px;
            margin: auto;
            background: white;
            padding: 28px;
            border-radius: 16px;
            box-shadow: 0 5px 24px #00000010;
        }
        h1 { color: #123b70; margin-bottom: 8px; }
        .note { color: #64748b; margin-bottom: 24px; }
        .grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 18px;
        }
        label { display: block; font-weight: bold; margin-bottom: 7px; }
        select, input {
            width: 100%;
            box-sizing: border-box;
            padding: 11px;
            border: 1px solid #cbd5e1;
            border-radius: 7px;
            font-size: 15px;
        }
        button {
            margin-top: 24px;
            padding: 13px 20px;
            background: #123b70;
            color: white;
            border: 0;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
        }
        .result {
            margin-top: 24px;
            padding: 18px;
            background: #eef6ff;
            border-radius: 8px;
            line-height: 1.6;
        }
        .disclaimer { margin-top: 24px; font-size: 13px; color: #64748b; }
        @media (max-width: 560px) {
            .grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
<div class="container">
    <h1>Home Credit</h1>
    <h2>Loan Against Property (LAP)</h2>
    <p class="note">Local prototype for testing eligibility business rules.</p>

    <form method="post">
        <div class="grid">
            <div>
                <label for="property_type">Property type</label>
                <select id="property_type" name="property_type" required>
                    <option value="Residential">Residential</option>
                    <option value="Commercial">Commercial</option>
                    <option value="Agricultural">Agricultural</option>
                    <option value="Industrial">Industrial</option>
                </select>
            </div>
            <div>
                <label for="ownership">Ownership</label>
                <select id="ownership" name="ownership" required>
                    <option value="Sole">Sole owner</option>
                    <option value="Joint">Joint ownership</option>
                </select>
            </div>
            <div>
                <label for="documents">Original documents</label>
                <select id="documents" name="documents" required>
                    <option value="Available">Available</option>
                    <option value="Unavailable">Unavailable</option>
                    <option value="Held by lender">Held by existing lender</option>
                </select>
            </div>
            <div>
                <label for="occupation">Income source</label>
                <select id="occupation" name="occupation" required>
                    <option value="Salaried bank credited">Salaried, bank-credited</option>
                    <option value="Self-employed bank credited">Self-employed, bank-credited</option>
                    <option value="Cash income">Cash income</option>
                </select>
            </div>
            <div>
                <label for="loan_amount">Requested loan (₹)</label>
                <input id="loan_amount" name="loan_amount" type="number"
                       min="1" step="1" max="100000000"
                       value="2500000" required>
            </div>
            <div>
                <label for="property_value">Estimated property value (₹)</label>
                <input id="property_value" name="property_value" type="number"
                       min="0" step="1" value="5000000" required>
            </div>
            <div>
                <label for="tenure">Tenure (years)</label>
                <input id="tenure" name="tenure" type="number"
                       min="1" max="40" step="1" value="10" required>
            </div>
        </div>
        <button type="submit">Check eligibility</button>
    </form>

    {% if result %}
    <div class="result" role="status">
        <h3>Demo result: {{ result.title }}</h3>
        <p>{{ result.message }}</p>
    </div>
    {% endif %}

    <p class="disclaimer">
        Demonstration only. This is not a credit decision, loan approval,
        or connection to Home Credit systems or the Retell voice agent.
        Use synthetic test data only.
    </p>
</div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    result = None

    if request.method == "POST":
        property_type = request.form.get("property_type", "").strip()
        ownership = request.form.get("ownership", "").strip()
        documents = request.form.get("documents", "").strip()
        occupation = request.form.get("occupation", "").strip()

        try:
            loan_amount = int(request.form.get("loan_amount", "0").strip().replace(",", ""))
            property_value = int(request.form.get("property_value", "0").strip().replace(",", ""))
            tenure = int(request.form.get("tenure", "0").strip().replace(",", ""))
        except (ValueError, TypeError):
            result = {
                "title": "Invalid input",
                "message": "Loan amount, property value, and tenure must be valid whole numbers."
            }
            return render_template_string(HTML, result=result)

        if property_type not in ("Residential", "Commercial"):
            result = {
                "title": "Disqualified",
                "message": "Only residential and commercial properties are eligible."
            }
        elif ownership not in ("Sole", "Joint"):
            result = {
                "title": "Disqualified",
                "message": "The ownership information does not meet the criteria."
            }
        elif documents == "Held by lender":
            result = {
                "title": "Specialist referral",
                "message": "The original documents are held by an existing lender. "
                           "Refer this case to a loan-transfer specialist."
            }
        elif documents != "Available":
            result = {
                "title": "Disqualified",
                "message": "Original property documents must be available."
            }
        elif occupation == "Cash income":
            result = {
                "title": "Disqualified",
                "message": "Income must be credited to a bank account."
            }
        elif occupation not in ("Salaried bank credited", "Self-employed bank credited"):
            result = {
                "title": "Need more information",
                "message": "Please confirm the income source."
            }
        elif not 1 <= loan_amount <= 100000000:
            result = {
                "title": "Invalid input",
                "message": "Enter a valid positive loan amount."
            }
        elif loan_amount > 7500000:
            result = {
                "title": "Loan amount exceeds cap",
                "message": "The maximum offer is ₹75,00,000. Ask whether the customer "
                           "wants to proceed within this limit."
            }
        elif tenure < 3 or tenure > 15:
            result = {
                "title": "Disqualified",
                "message": "The eligible tenure range is 3 to 15 years."
            }
        elif property_value < 0:
            result = {
                "title": "Invalid input",
                "message": "Property value cannot be negative."
            }
        else:
            result = {
                "title": "Potentially eligible",
                "message": "The entered details pass these basic demo checks. "
                           "A senior loan expert must verify the details, rates, "
                           "and next steps. This is not loan approval."
            }

    return render_template_string(HTML, result=result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1")
    app.run(host="0.0.0.0", port=port, debug=debug)


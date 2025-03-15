from django.shortcuts import render, redirect
from django.db import connection  # Connect to MySQL RDS
from django.contrib import messages

def branch_login(request):
    BranchName = None
    if request.method == "POST":
        if "IFSC_CODE" in request.POST:
            # Fetch branch details
            IFSC_CODE = request.POST.get("IFSC_CODE")

            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT BranchName FROM Branches WHERE IFSC_Code = %s",
                    [IFSC_CODE]
                )
                result = cursor.fetchone()

            if result:
                BranchName = result[0]  # Fetch branch name
                request.session['BranchName'] = BranchName
                request.session['IFSC_CODE'] = IFSC_CODE
            else:
                messages.error(request, "Invalid IFSC Code")
                return render(request, "branch_login.html")

    return render(request, "branch_login.html", {"BranchName": BranchName})

def employee_login(request):
    BranchName = request.session.get('BranchName')
    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        password = request.POST.get("password")

        if employee_id == "ubi" and password == "ubi":
            request.session['user_role'] = 'employee'
            return redirect("/dashboard/")
        else:
            messages.error(request, "Invalid Employee Credentials")

    return render(request, "employee_login.html", {"BranchName": BranchName})

def compliance_login(request):
    BranchName = request.session.get('BranchName')
    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        password = request.POST.get("password")

        if employee_id == "transactionteam" and password == "ubi":
            request.session['user_role'] = 'compliance'
            return redirect("/dashboard/")
        else:
            messages.error(request, "Invalid Compliance Team Credentials")

    return render(request, "compliance_login.html", {"BranchName": BranchName})

def dashboard(request):
    user_role = request.session.get('user_role')
    return render(request, 'dashboard.html', {'user_role': user_role})

def compliance_dashboard(request):
    return render(request, 'compliance_dashboard.html')

def fraud_detection(request):
    return render(request, 'fraud_detection.html')

def risk_scoring(request):
    return render(request, 'risk_scoring.html')

def pattern_analysis(request):
    return render(request, 'pattern_analysis.html')

def insider_threat(request):
    return render(request, 'insider_threat.html')

def reports(request):
    return render(request, 'reports.html')

def mail(request):
    return render(request, 'mail.html')

def crm(request):
    return render(request, 'crm.html')

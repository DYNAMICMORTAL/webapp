from django.shortcuts import render, redirect
from django.db import connection  # Connect to MySQL RDS
from django.contrib import messages

def branch_login(request):
    BranchName = None
    if request.method == "POST":
        if "IFSC_CODE" in request.POST:
            # Fetch branch details
            # branch_number = request.POST.get("branch_number")
            IFSC_CODE = request.POST.get("IFSC_CODE")

            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT BranchName FROM Branches WHERE IFSC_Code = %s",
                    [IFSC_CODE]
                )
                result = cursor.fetchone()

            if result:
                BranchName = result[0]  # Fetch branch name
            else:
                messages.error(request, "Invalid IFSC Code")
                return render(request, "branch_login.html")

        elif "employee_id" in request.POST and "password" in request.POST:
            # Employee Login Validation
            employee_id = request.POST.get("employee_id")
            password = request.POST.get("password")

            if employee_id == "ubi" and password == "ubi":
                return redirect("/customers/search/")
            else:
                messages.error(request, "Invalid Employee Credentials")

    return render(request, "branch_login.html", {"BranchName": BranchName})

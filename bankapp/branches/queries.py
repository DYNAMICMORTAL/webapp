AGE_GROUP_QUERY = """
    SELECT 
        CASE 
            WHEN TIMESTAMPDIFF(YEAR, DateOfBirth, CURDATE()) < 18 THEN 'Under 18'
            WHEN TIMESTAMPDIFF(YEAR, DateOfBirth, CURDATE()) BETWEEN 18 AND 25 THEN '18-25'
            WHEN TIMESTAMPDIFF(YEAR, DateOfBirth, CURDATE()) BETWEEN 26 AND 35 THEN '26-35'
            WHEN TIMESTAMPDIFF(YEAR, DateOfBirth, CURDATE()) BETWEEN 36 AND 45 THEN '36-45'
            WHEN TIMESTAMPDIFF(YEAR, DateOfBirth, CURDATE()) BETWEEN 46 AND 55 THEN '46-55'
            WHEN TIMESTAMPDIFF(YEAR, DateOfBirth, CURDATE()) BETWEEN 56 AND 65 THEN '56-65'
            ELSE '65+'
        END AS AgeGroup,
        COUNT(*) AS CustomerCount,
        AVG(a.Balance) AS AvgBalance,
        SUM(a.Balance) AS TotalBalance,
        COUNT(DISTINCT l.LoanID) AS TotalLoans,
        COUNT(DISTINCT cc.CardID) AS TotalCreditCards,
        GROUP_CONCAT(c.CustomerID) AS CustomerIDs
    FROM 
        Customers c
    LEFT JOIN 
        Accounts a ON c.CustomerID = a.CustomerID
    LEFT JOIN 
        Loans l ON c.CustomerID = l.CustomerID
    LEFT JOIN 
        CreditCards cc ON c.CustomerID = cc.CustomerID
    GROUP BY 
        AgeGroup
    ORDER BY 
        CASE 
            WHEN AgeGroup = 'Under 18' THEN 1
            WHEN AgeGroup = '18-25' THEN 2
            WHEN AgeGroup = '26-35' THEN 3
            WHEN AgeGroup = '36-45' THEN 4
            WHEN AgeGroup = '46-55' THEN 5
            WHEN AgeGroup = '56-65' THEN 6
            WHEN AgeGroup = '65+' THEN 7
    END;
"""

GEOGRAPHIC_QUERY = """
SELECT 
    State,
    City,
    COUNT(*) AS CustomerCount,
    COUNT(DISTINCT a.AccountID) AS TotalAccounts,
    AVG(a.Balance) AS AvgBalance,
    SUM(a.Balance) AS TotalBalance
FROM 
    Customers c
LEFT JOIN 
    Accounts a ON c.CustomerID = a.CustomerID
GROUP BY 
    State, City
ORDER BY 
    CustomerCount DESC;"""

REGIONAL_STATE_QUERY = """SELECT 
    State,
    COUNT(*) AS CustomerCount,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM Customers), 2) AS CustomerPercentage,
    COUNT(DISTINCT a.AccountID) AS TotalAccounts,
    SUM(a.Balance) AS TotalDeposits,
    ROUND(SUM(a.Balance) * 100.0 / (SELECT SUM(Balance) FROM Accounts), 2) AS DepositPercentage
FROM 
    Customers c
LEFT JOIN 
    Accounts a ON c.CustomerID = a.CustomerID
GROUP BY 
    State
ORDER BY 
    TotalDeposits DESC;"""

ACCOUNT_TYPE_QUERY = """SELECT 
    a.AccountType,
    COUNT(*) AS AccountCount,
    COUNT(DISTINCT a.CustomerID) AS CustomerCount,
    AVG(a.Balance) AS AvgBalance,
    SUM(a.Balance) AS TotalBalance
FROM 
    Accounts a
GROUP BY 
    a.AccountType
ORDER BY 
    AccountCount DESC;
"""

MULTI_PRODUCT_QUERY = """SELECT 
    ProductCount,
    COUNT(*) AS CustomerCount,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM Customers), 2) AS CustomerPercentage
FROM (
    SELECT 
        c.CustomerID,
        (CASE WHEN COUNT(DISTINCT a.AccountID) > 0 THEN 1 ELSE 0 END +
         CASE WHEN COUNT(DISTINCT l.LoanID) > 0 THEN 1 ELSE 0 END +
         CASE WHEN COUNT(DISTINCT m.MortgageID) > 0 THEN 1 ELSE 0 END +
         CASE WHEN COUNT(DISTINCT cc.CardID) > 0 THEN 1 ELSE 0 END) AS ProductCount
    FROM 
        Customers c
    LEFT JOIN 
        Accounts a ON c.CustomerID = a.CustomerID
    LEFT JOIN 
        Loans l ON c.CustomerID = l.CustomerID
    LEFT JOIN 
        Mortgages m ON c.CustomerID = m.CustomerID
    LEFT JOIN 
        CreditCards cc ON c.CustomerID = cc.CustomerID
    GROUP BY 
        c.CustomerID
) AS ProductCounts
GROUP BY 
    ProductCount
ORDER BY 
    ProductCount;"""

BALANCE_TIERS_QUERY = """SELECT 
    CASE 
        WHEN Balance = 0 THEN 'Zero Balance'
        WHEN Balance BETWEEN 0.01 AND 10000 THEN 'Low (0.01-10K)'
        WHEN Balance BETWEEN 10000.01 AND 50000 THEN 'Medium (10K-50K)'
        WHEN Balance BETWEEN 50000.01 AND 100000 THEN 'High (50K-100K)'
        WHEN Balance BETWEEN 100000.01 AND 500000 THEN 'Very High (100K-500K)'
        ELSE 'Ultra High (500K+)'
    END AS BalanceTier,
    COUNT(*) AS AccountCount,
    COUNT(DISTINCT CustomerID) AS CustomerCount,
    AVG(Balance) AS AvgBalance,
    SUM(Balance) AS TotalBalance
FROM 
    Accounts
GROUP BY 
    BalanceTier
ORDER BY 
    CASE 
        WHEN BalanceTier = 'Zero Balance' THEN 0
        WHEN BalanceTier = 'Low (0.01-10K)' THEN 1
        WHEN BalanceTier = 'Medium (10K-50K)' THEN 2
        WHEN BalanceTier = 'High (50K-100K)' THEN 3
        WHEN BalanceTier = 'Very High (100K-500K)' THEN 4
        WHEN BalanceTier = 'Ultra High (500K+)' THEN 5
    END;"""


CREDIT_CARD_USERS_QUERY = """SELECT 
    CASE 
        WHEN cc.CardID IS NULL THEN 'Non-Credit Card Users'
        ELSE 'Credit Card Users'
    END AS CreditCardSegment,
    COUNT(DISTINCT c.CustomerID) AS CustomerCount,
    ROUND(COUNT(DISTINCT c.CustomerID) * 100.0 / (SELECT COUNT(*) FROM Customers), 2) AS CustomerPercentage,
    AVG(a.Balance) AS AvgAccountBalance,
    COUNT(DISTINCT a.AccountID) / COUNT(DISTINCT c.CustomerID) AS AvgAccountsPerCustomer
FROM 
    Customers c
LEFT JOIN 
    CreditCards cc ON c.CustomerID = cc.CustomerID
LEFT JOIN 
    Accounts a ON c.CustomerID = a.CustomerID
GROUP BY 
    CreditCardSegment;"""


LOAN_PORTFOLIO_QUERY = """SELECT 
    l.LoanType,
    COUNT(*) AS LoanCount,
    COUNT(DISTINCT l.CustomerID) AS CustomerCount,
    AVG(l.LoanAmount) AS AvgLoanAmount,
    SUM(l.LoanAmount) AS TotalLoanAmount,
    AVG(l.InterestRate) AS AvgInterestRate,
    AVG(l.LoanTerm) AS AvgLoanTermMonths
FROM 
    Loans l
GROUP BY 
    l.LoanType
ORDER BY 
    LoanCount DESC;"""

MORTGAGE_HOLDERS_QUERY = """SELECT 
    CASE 
        WHEN m.MortgageID IS NULL THEN 'Non-Mortgage Holders'
        ELSE 'Mortgage Holders'
    END AS MortgageSegment,
    COUNT(DISTINCT c.CustomerID) AS CustomerCount,
    ROUND(COUNT(DISTINCT c.CustomerID) * 100.0 / (SELECT COUNT(*) FROM Customers), 2) AS CustomerPercentage,
    AVG(a.Balance) AS AvgAccountBalance,
    AVG(l.LoanAmount) AS AvgOtherLoanAmount,
    COUNT(DISTINCT cc.CardID) / NULLIF(COUNT(DISTINCT CASE WHEN m.MortgageID IS NOT NULL THEN c.CustomerID END), 0) AS AvgCreditCardsPerMortgageHolder
FROM 
    Customers c
LEFT JOIN 
    Mortgages m ON c.CustomerID = m.CustomerID
LEFT JOIN 
    Accounts a ON c.CustomerID = a.CustomerID
LEFT JOIN 
    Loans l ON c.CustomerID = l.CustomerID AND l.LoanType != 'Home'
LEFT JOIN 
    CreditCards cc ON c.CustomerID = cc.CustomerID
GROUP BY 
    MortgageSegment;"""

CREDIT_CARD_PREFERENCES_QUERY = """SELECT 
    cc.CardType,
    COUNT(*) AS CardCount,
    COUNT(DISTINCT cc.CustomerID) AS CustomerCount,
    AVG(cc.CreditLimit) AS AvgCreditLimit,
    MAX(cc.CreditLimit) AS MaxCreditLimit,
    MIN(cc.CreditLimit) AS MinCreditLimit
FROM 
    CreditCards cc
GROUP BY 
    cc.CardType
ORDER BY 
    CardCount DESC;"""

CREDIT_LIMIT_UTILIZATION_QUERY = """SELECT 
    CASE 
        WHEN cc.CreditLimit <= 50000 THEN 'Low Limit (<= 50K)'
        WHEN cc.CreditLimit BETWEEN 50001 AND 100000 THEN 'Medium Limit (50K-100K)'
        WHEN cc.CreditLimit BETWEEN 100001 AND 250000 THEN 'High Limit (100K-250K)'
        ELSE 'Premium Limit (>250K)'
    END AS CreditLimitTier,
    COUNT(*) AS CardCount,
    COUNT(DISTINCT cc.CustomerID) AS CustomerCount,
    AVG(cc.CreditLimit) AS AvgCreditLimit,
    AVG(a.Balance) AS AvgAccountBalance
FROM 
    CreditCards cc
LEFT JOIN 
    Customers c ON cc.CustomerID = c.CustomerID
LEFT JOIN 
    Accounts a ON c.CustomerID = a.CustomerID
GROUP BY 
    CreditLimitTier
ORDER BY 
    CASE 
        WHEN CreditLimitTier = 'Low Limit (<= 50K)' THEN 1
        WHEN CreditLimitTier = 'Medium Limit (50K-100K)' THEN 2
        WHEN CreditLimitTier = 'High Limit (100K-250K)' THEN 3
        WHEN CreditLimitTier = 'Premium Limit (>250K)' THEN 4
    END;"""

CUSTOMER_LIFETIME_VALUE_QUERY = """WITH CustomerValue AS (
    SELECT 
        c.CustomerID,
        c.FirstName,
        c.LastName,
        SUM(a.Balance) AS TotalDeposits,
        SUM(l.LoanAmount) AS TotalLoans,
        SUM(m.LoanAmount) AS TotalMortgages,
        SUM(cc.CreditLimit) AS TotalCreditLimit,
        DATEDIFF(CURDATE(), c.CreatedAt) AS CustomerTenureDays
    FROM 
        Customers c
    LEFT JOIN 
        Accounts a ON c.CustomerID = a.CustomerID
    LEFT JOIN 
        Loans l ON c.CustomerID = l.CustomerID
    LEFT JOIN 
        Mortgages m ON c.CustomerID = m.CustomerID
    LEFT JOIN 
        CreditCards cc ON c.CustomerID = cc.CustomerID
    GROUP BY 
        c.CustomerID, c.FirstName, c.LastName, c.CreatedAt
)
SELECT 
    CustomerID,
    FirstName,
    LastName,
    ROUND(CustomerTenureDays / 365.25, 1) AS TenureYears,
    TotalDeposits,
    TotalLoans,
    TotalMortgages,
    TotalCreditLimit,
    (COALESCE(TotalDeposits, 0) * 0.02 + 
     COALESCE(TotalLoans, 0) * 0.05 + 
     COALESCE(TotalMortgages, 0) * 0.03 + 
     COALESCE(TotalCreditLimit, 0) * 0.01) AS EstimatedAnnualValue,
    (COALESCE(TotalDeposits, 0) * 0.02 + 
     COALESCE(TotalLoans, 0) * 0.05 + 
     COALESCE(TotalMortgages, 0) * 0.03 + 
     COALESCE(TotalCreditLimit, 0) * 0.01) * 
     CASE 
         WHEN CustomerTenureDays <= 365 THEN 5
         WHEN CustomerTenureDays BETWEEN 366 AND 1095 THEN 4
         ELSE 3
     END AS EstimatedLifetimeValue
FROM 
    CustomerValue
ORDER BY 
    EstimatedLifetimeValue DESC
LIMIT 100;"""

HIGH_NET_WORTH_INDIVIDUALS_QUERY = """WITH CustomerNetWorth AS (
    SELECT 
        c.CustomerID,
        c.FirstName,
        c.LastName,
        c.City,
        c.State,
        SUM(a.Balance) AS TotalDeposits,
        COUNT(DISTINCT a.AccountID) AS AccountCount,
        COUNT(DISTINCT l.LoanID) AS LoanCount,
        COUNT(DISTINCT m.MortgageID) AS MortgageCount,
        COUNT(DISTINCT cc.CardID) AS CreditCardCount
    FROM 
        Customers c
    LEFT JOIN 
        Accounts a ON c.CustomerID = a.CustomerID
    LEFT JOIN 
        Loans l ON c.CustomerID = l.CustomerID
    LEFT JOIN 
        Mortgages m ON c.CustomerID = m.CustomerID
    LEFT JOIN 
        CreditCards cc ON c.CustomerID = cc.CustomerID
    GROUP BY 
        c.CustomerID, c.FirstName, c.LastName, c.City, c.State
)
SELECT 
    CASE 
        WHEN TotalDeposits >= 1000000 THEN 'Ultra-High Net Worth (1M+)'
        WHEN TotalDeposits BETWEEN 500000 AND 999999.99 THEN 'Very High Net Worth (500K-1M)'
        WHEN TotalDeposits BETWEEN 100000 AND 499999.99 THEN 'High Net Worth (100K-500K)'
        WHEN TotalDeposits BETWEEN 50000 AND 99999.99 THEN 'Affluent (50K-100K)'
        WHEN TotalDeposits BETWEEN 10000 AND 49999.99 THEN 'Mass Affluent (10K-50K)'
        ELSE 'Mass Market (<10K)'
    END AS WealthSegment,
    COUNT(*) AS CustomerCount,
    AVG(TotalDeposits) AS AvgDeposits,
    AVG(AccountCount) AS AvgAccounts,
    AVG(LoanCount) AS AvgLoans,
    AVG(MortgageCount) AS AvgMortgages,
    AVG(CreditCardCount) AS AvgCreditCards
FROM 
    CustomerNetWorth
GROUP BY 
    WealthSegment
ORDER BY 
    CASE 
        WHEN WealthSegment = 'Ultra-High Net Worth (1M+)' THEN 1
        WHEN WealthSegment = 'Very High Net Worth (500K-1M)' THEN 2
        WHEN WealthSegment = 'High Net Worth (100K-500K)' THEN 3
        WHEN WealthSegment = 'Affluent (50K-100K)' THEN 4
        WHEN WealthSegment = 'Mass Affluent (10K-50K)' THEN 5
        WHEN WealthSegment = 'Mass Market (<10K)' THEN 6
    END;"""


CROSS_SELLING_POTENTIAL_QUERY = """SELECT 
    c.CustomerID,
    c.FirstName,
    c.LastName,
    CASE WHEN COUNT(DISTINCT a.AccountID) > 0 THEN 'Yes' ELSE 'No' END AS HasAccount,
    CASE WHEN COUNT(DISTINCT l.LoanID) > 0 THEN 'Yes' ELSE 'No' END AS HasLoan,
    CASE WHEN COUNT(DISTINCT m.MortgageID) > 0 THEN 'Yes' ELSE 'No' END AS HasMortgage,
    CASE WHEN COUNT(DISTINCT cc.CardID) > 0 THEN 'Yes' ELSE 'No' END AS HasCreditCard,
    CASE 
        WHEN COUNT(DISTINCT a.AccountID) > 0 AND COUNT(DISTINCT l.LoanID) = 0 AND COUNT(DISTINCT cc.CardID) = 0 THEN 'Loan and Credit Card'
        WHEN COUNT(DISTINCT a.AccountID) > 0 AND COUNT(DISTINCT cc.CardID) = 0 THEN 'Credit Card'
        WHEN COUNT(DISTINCT a.AccountID) > 0 AND COUNT(DISTINCT l.LoanID) = 0 THEN 'Loan'
        WHEN COUNT(DISTINCT l.LoanID) > 0 AND COUNT(DISTINCT cc.CardID) = 0 THEN 'Credit Card'
        WHEN COUNT(DISTINCT cc.CardID) > 0 AND COUNT(DISTINCT l.LoanID) = 0 THEN 'Loan'
        ELSE 'Full Relationship'
    END AS CrossSellingOpportunity
FROM 
    Customers c
LEFT JOIN 
    Accounts a ON c.CustomerID = a.CustomerID
LEFT JOIN 
    Loans l ON c.CustomerID = l.CustomerID
LEFT JOIN 
    Mortgages m ON c.CustomerID = m.CustomerID
LEFT JOIN 
    CreditCards cc ON c.CustomerID = cc.CustomerID
GROUP BY 
    c.CustomerID, c.FirstName, c.LastName
ORDER BY 
    CASE 
        WHEN CrossSellingOpportunity = 'Loan and Credit Card' THEN 1
        WHEN CrossSellingOpportunity = 'Credit Card' THEN 2
        WHEN CrossSellingOpportunity = 'Loan' THEN 3
        WHEN CrossSellingOpportunity = 'Full Relationship' THEN 4
    END;"""

LOAN_STATUS_PROFILE_QUERY = """SELECT 
    l.Status,
    COUNT(*) AS LoanCount,
    COUNT(DISTINCT l.CustomerID) AS CustomerCount,
    AVG(l.LoanAmount) AS AvgLoanAmount,
    SUM(l.LoanAmount) AS TotalLoanAmount,
    AVG(l.InterestRate) AS AvgInterestRate
FROM 
    Loans l
GROUP BY 
    l.Status;"""

CREDIT_RISK_CATEGORIES_QUERY = """WITH CustomerRisk AS (
    SELECT 
        c.CustomerID,
        COUNT(DISTINCT l.LoanID) AS LoanCount,
        SUM(l.LoanAmount) AS TotalLoanAmount,
        MAX(cc.CreditLimit) AS MaxCreditLimit,
        AVG(a.Balance) AS AvgAccountBalance,
        SUM(a.Balance) AS TotalBalance,
        SUM(l.LoanAmount) / NULLIF(SUM(a.Balance), 0) AS DebtToDepositRatio
    FROM 
        Customers c
    LEFT JOIN 
        Loans l ON c.CustomerID = l.CustomerID
    LEFT JOIN 
        CreditCards cc ON c.CustomerID = cc.CustomerID
    LEFT JOIN 
        Accounts a ON c.CustomerID = a.CustomerID
    GROUP BY 
        c.CustomerID
)
SELECT 
    CASE 
        WHEN DebtToDepositRatio IS NULL THEN 'No Debt'
        WHEN DebtToDepositRatio <= 0.2 THEN 'Very Low Risk'
        WHEN DebtToDepositRatio <= 0.5 THEN 'Low Risk'
        WHEN DebtToDepositRatio <= 1 THEN 'Moderate Risk'
        WHEN DebtToDepositRatio <= 2 THEN 'High Risk'
        ELSE 'Very High Risk'
    END AS RiskCategory,
    COUNT(*) AS CustomerCount,
    AVG(TotalLoanAmount) AS AvgDebt,
    AVG(TotalBalance) AS AvgDeposits,
    AVG(DebtToDepositRatio) AS AvgDebtToDepositRatio
FROM 
    CustomerRisk
GROUP BY 
    RiskCategory
ORDER BY 
    CASE 
        WHEN RiskCategory = 'No Debt' THEN 0
        WHEN RiskCategory = 'Very Low Risk' THEN 1
        WHEN RiskCategory = 'Low Risk' THEN 2
        WHEN RiskCategory = 'Moderate Risk' THEN 3
        WHEN RiskCategory = 'High Risk' THEN 4
        WHEN RiskCategory = 'Very High Risk' THEN 5
    END;"""

RELATIONSHIP_TENURE_QUERY = """SELECT 
    CASE 
        WHEN DATEDIFF(CURDATE(), c.CreatedAt) <= 30 THEN 'New (0-30 days)'
        WHEN DATEDIFF(CURDATE(), c.CreatedAt) <= 90 THEN 'Recent (1-3 months)'
        WHEN DATEDIFF(CURDATE(), c.CreatedAt) <= 365 THEN 'Established (3-12 months)'
        WHEN DATEDIFF(CURDATE(), c.CreatedAt) <= 1095 THEN 'Loyal (1-3 years)'
        ELSE 'Long-term (3+ years)'
    END AS TenureSegment,
    COUNT(*) AS CustomerCount,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM Customers), 2) AS CustomerPercentage,
    AVG(a.Balance) AS AvgBalance,
    COUNT(DISTINCT l.LoanID) / COUNT(DISTINCT c.CustomerID) AS LoansPerCustomer,
    COUNT(DISTINCT cc.CardID) / COUNT(DISTINCT c.CustomerID) AS CardsPerCustomer
FROM 
    Customers c
LEFT JOIN 
    Accounts a ON c.CustomerID = a.CustomerID
LEFT JOIN 
    Loans l ON c.CustomerID = l.CustomerID
LEFT JOIN 
    CreditCards cc ON c.CustomerID = cc.CustomerID
GROUP BY 
    TenureSegment
ORDER BY 
    CASE 
        WHEN TenureSegment = 'New (0-30 days)' THEN 1
        WHEN TenureSegment = 'Recent (1-3 months)' THEN 2
        WHEN TenureSegment = 'Established (3-12 months)' THEN 3
        WHEN TenureSegment = 'Loyal (1-3 years)' THEN 4
        WHEN TenureSegment = 'Long-term (3+ years)' THEN 5
    END;"""

BRANCH_RELATIONSHIP_QUERY = """SELECT 
    b.BranchName,
    b.City,
    b.State,
    COUNT(DISTINCT a.CustomerID) AS CustomerCount,
    COUNT(DISTINCT a.AccountID) AS AccountCount,
    COUNT(DISTINCT a.AccountID) / COUNT(DISTINCT a.CustomerID) AS AccountsPerCustomer,
    AVG(a.Balance) AS AvgBalance,
    SUM(a.Balance) AS TotalDeposits
FROM 
    Branches b
LEFT JOIN 
    Accounts a ON b.BranchID = a.BranchID
GROUP BY 
    b.BranchID, b.BranchName, b.City, b.State
ORDER BY 
    CustomerCount DESC;"""

PRODUCT_ADOPTION_TIMELINE_QUERY = """SELECT 
    c.CustomerID,
    c.FirstName,
    c.LastName,
    c.CreatedAt AS CustomerSince,
    MIN(a.CreatedAt) AS FirstAccountDate,
    DATEDIFF(MIN(a.CreatedAt), c.CreatedAt) AS DaysToFirstAccount,
    MIN(l.StartDate) AS FirstLoanDate,
    DATEDIFF(MIN(l.StartDate), c.CreatedAt) AS DaysToFirstLoan,
    MIN(cc.ExpiryDate - INTERVAL 3 YEAR) AS FirstCreditCardDate, -- Approximating by assuming 3-year validity
    CASE 
        WHEN MIN(a.CreatedAt) IS NULL THEN 'No Products'
        WHEN DATEDIFF(MIN(a.CreatedAt), c.CreatedAt) <= 7 THEN 'Immediate Adoption'
        WHEN DATEDIFF(MIN(a.CreatedAt), c.CreatedAt) <= 30 THEN 'Quick Adoption'
        WHEN DATEDIFF(MIN(a.CreatedAt), c.CreatedAt) <= 90 THEN 'Normal Adoption'
        ELSE 'Delayed Adoption'
    END AS AdoptionSpeed
FROM 
    Customers c
LEFT JOIN 
    Accounts a ON c.CustomerID = a.CustomerID
LEFT JOIN 
    Loans l ON c.CustomerID = l.CustomerID
LEFT JOIN 
    CreditCards cc ON c.CustomerID = cc.CustomerID
GROUP BY 
    c.CustomerID, c.FirstName, c.LastName, c.CreatedAt
ORDER BY 
    c.CreatedAt DESC;"""

RFM_SEGMENTATION_QUERY = """WITH CustomerRFM AS (
    SELECT 
        c.CustomerID,
        c.FirstName,
        c.LastName,
        -- Recency (using CreatedAt as a proxy since we don't have transaction data)
        DATEDIFF(CURDATE(), c.CreatedAt) AS DaysSinceJoining,
        DATEDIFF(CURDATE(), GREATEST(COALESCE(MAX(a.CreatedAt), '1970-01-01'), 
                                      COALESCE(MAX(l.StartDate), '1970-01-01'))) AS DaysSinceLastActivity,
        -- Frequency (product count)
        COUNT(DISTINCT a.AccountID) + 
        COUNT(DISTINCT l.LoanID) + 
        COUNT(DISTINCT m.MortgageID) + 
        COUNT(DISTINCT cc.CardID) AS TotalProducts,
        -- Monetary
        COALESCE(SUM(a.Balance), 0) AS TotalDeposits,
        COALESCE(SUM(l.LoanAmount), 0) + COALESCE(SUM(m.LoanAmount), 0) AS TotalLoanAmount,
        COALESCE(SUM(cc.CreditLimit), 0) AS TotalCreditLimit
    FROM 
        Customers c
    LEFT JOIN 
        Accounts a ON c.CustomerID = a.CustomerID
    LEFT JOIN 
        Loans l ON c.CustomerID = l.CustomerID
    LEFT JOIN 
        Mortgages m ON c.CustomerID = m.CustomerID
    LEFT JOIN 
        CreditCards cc ON c.CustomerID = cc.CustomerID
    GROUP BY 
        c.CustomerID, c.FirstName, c.LastName, c.CreatedAt
),
RFMScores AS (
    SELECT 
        *,
        -- R Score (1-5, 5 being most recent)
        NTILE(5) OVER (ORDER BY DaysSinceLastActivity DESC) AS R_Score,
        -- F Score (1-5, 5 being most frequent)
        NTILE(5) OVER (ORDER BY TotalProducts) AS F_Score,
        -- M Score (1-5, 5 being highest value)
        NTILE(5) OVER (ORDER BY (TotalDeposits + TotalCreditLimit - TotalLoanAmount)) AS M_Score
    FROM 
        CustomerRFM
)
SELECT 
    CustomerID,
    FirstName,
    LastName,
    DaysSinceJoining,
    DaysSinceLastActivity,
    TotalProducts,
    TotalDeposits,
    TotalLoanAmount,
    TotalCreditLimit,
    R_Score,
    F_Score,
    M_Score,
    CONCAT(R_Score, F_Score, M_Score) AS RFM_Score,
    CASE 
        WHEN (R_Score + F_Score + M_Score) >= 13 THEN 'Champions'
        WHEN (R_Score + F_Score + M_Score) >= 10 THEN 'Loyal Customers'
        WHEN (R_Score + F_Score + M_Score) >= 8 THEN 'Potential Loyalists'
        WHEN R_Score >= 4 AND (F_Score + M_Score) >= 4 THEN 'New High-Value Customers'
        WHEN R_Score >= 4 AND (F_Score + M_Score) < 4 THEN 'Promising New Customers'
        WHEN R_Score < 3 AND (F_Score + M_Score) >= 8 THEN 'At-Risk High-Value Customers'
        WHEN R_Score < 3 AND F_Score >= 4 AND M_Score < 4 THEN 'At-Risk Product-Focused Customers'
        WHEN R_Score < 3 AND F_Score < 4 AND M_Score >= 4 THEN 'At-Risk Value-Focused Customers'
        WHEN F_Score <= 2 AND M_Score <= 2 THEN 'Low-Value Customers'
        ELSE 'Average Customers'
    END AS CustomerSegment
FROM 
    RFMScores
ORDER BY 
    (R_Score + F_Score + M_Score) DESC;"""
# Exact Online REST API Endpoints

This document provides a categorized reference of the Exact Online REST API endpoints, organized by service.

> **Note:** Most resource URIs require a `{division}` parameter. You can retrieve the current division via `/api/v1/current/Me`.

---



## Accountancy


| Resource                | URI                                                      | Methods                |
| ----------------------- | -------------------------------------------------------- | ---------------------- |
| AccountInvolvedAccounts | `/api/v1/{division}/accountancy/AccountInvolvedAccounts` | GET, POST, PUT, DELETE |
| AccountOwners           | `/api/v1/{division}/accountancy/AccountOwners`           | GET, POST, PUT, DELETE |
| ClientGroups            | `/api/v1/{division}/accountancy/ClientGroups`            | GET                    |
| ClientMainGroups        | `/api/v1/{division}/accountancy/ClientMainGroups`        | GET                    |
| InvolvedUserRoles       | `/api/v1/{division}/accountancy/InvolvedUserRoles`       | GET, POST, PUT, DELETE |
| InvolvedUsers           | `/api/v1/{division}/accountancy/InvolvedUsers`           | GET, POST, PUT, DELETE |
| SolutionLinks           | `/api/v1/{division}/accountancy/SolutionLinks`           | GET, POST, PUT, DELETE |
| TaskTypes               | `/api/v1/{division}/accountancy/TaskTypes`               | GET, POST, PUT, DELETE |




## CRM


| Resource                   | URI                                                 | Methods                |
| -------------------------- | --------------------------------------------------- | ---------------------- |
| AcceptQuotation            | `/api/v1/{division}/crm/AcceptQuotation`            | POST                   |
| AccountClasses             | `/api/v1/{division}/crm/AccountClasses`             | GET                    |
| AccountClassificationNames | `/api/v1/{division}/crm/AccountClassificationNames` | GET                    |
| AccountClassifications     | `/api/v1/{division}/crm/AccountClassifications`     | GET                    |
| Accounts                   | `/api/v1/{division}/crm/Accounts`                   | GET, POST, PUT, DELETE |
| Addresses                  | `/api/v1/{division}/crm/Addresses`                  | GET, POST, PUT, DELETE |
| AddressStates              | `/api/v1/{division}/crm/AddressStates`              | GET                    |
| BankAccounts               | `/api/v1/{division}/crm/BankAccounts`               | GET, POST, PUT, DELETE |
| Contacts                   | `/api/v1/{division}/crm/Contacts`                   | GET, POST, PUT, DELETE |
| EmailWithSignOffQuotation  | `/api/v1/{division}/crm/EmailWithSignOffQuotation`  | POST                   |
| LeadPurposes               | `/api/v1/{division}/crm/LeadPurposes`               | GET                    |
| LeadSources                | `/api/v1/{division}/crm/LeadSources`                | GET                    |
| Opportunities              | `/api/v1/{division}/crm/Opportunities`              | GET, POST, PUT, DELETE |
| OptionalQuotationLineID    | `/api/v1/{division}/crm/OptionalQuotationLineID`    | POST                   |
| PrintQuotation             | `/api/v1/{division}/crm/PrintQuotation`             | POST                   |
| QuotationLines             | `/api/v1/{division}/crm/QuotationLines`             | GET, POST, PUT, DELETE |
| QuotationOrderChargeLines  | `/api/v1/{division}/crm/QuotationOrderChargeLines`  | GET, POST, PUT, DELETE |
| Quotations                 | `/api/v1/{division}/crm/Quotations`                 | GET, POST, PUT, DELETE |
| ReasonCodes                | `/api/v1/{division}/crm/ReasonCodes`                | GET                    |
| RejectQuotation            | `/api/v1/{division}/crm/RejectQuotation`            | POST                   |
| ReopenQuotation            | `/api/v1/{division}/crm/ReopenQuotation`            | POST                   |
| ReviewQuotation            | `/api/v1/{division}/crm/ReviewQuotation`            | POST                   |




## Financial


| Resource                        | URI                                                            | Methods                |
| ------------------------------- | -------------------------------------------------------------- | ---------------------- |
| DeductibilityPercentages        | `/api/v1/{division}/financial/DeductibilityPercentages`        | GET                    |
| ExchangeRates                   | `/api/v1/{division}/financial/ExchangeRates`                   | GET, POST, PUT, DELETE |
| FinancialPeriods                | `/api/v1/{division}/financial/FinancialPeriods`                | GET                    |
| GLAccountClassificationMappings | `/api/v1/{division}/financial/GLAccountClassificationMappings` | GET, POST, PUT, DELETE |
| GLAccounts                      | `/api/v1/{division}/financial/GLAccounts`                      | GET, POST, PUT, DELETE |
| GLClassifications               | `/api/v1/{division}/financial/GLClassifications`               | GET                    |
| GLSchemes                       | `/api/v1/{division}/financial/GLSchemes`                       | GET                    |
| GLTransactionSources            | `/api/v1/{division}/financial/GLTransactionSources`            | GET                    |
| GLTransactionTypes              | `/api/v1/{division}/financial/GLTransactionTypes`              | GET                    |
| Journals                        | `/api/v1/{division}/financial/Journals`                        | GET, POST, PUT, DELETE |
| OfficialReturns                 | `/api/v1/{division}/financial/OfficialReturns`                 | GET, POST              |
| ProcessReturn                   | `/api/v1/{division}/financial/ProcessReturn`                   | POST                   |




## Logistics & Inventory


| Resource                        | URI                                                            | Methods                |
| ------------------------------- | -------------------------------------------------------------- | ---------------------- |
| AssemblyBillOfMaterialHeader    | `/api/v1/{division}/inventory/AssemblyBillOfMaterialHeader`    | GET, POST, PUT, DELETE |
| AssemblyBillOfMaterialMaterials | `/api/v1/{division}/inventory/AssemblyBillOfMaterialMaterials` | GET, POST, PUT, DELETE |
| Items                           | `/api/v1/{division}/logistics/Items`                           | GET, POST, PUT, DELETE |
| SalesItemPrices                 | `/api/v1/{division}/logistics/SalesItemPrices`                 | GET, POST, PUT, DELETE |
| Warehouses                      | `/api/v1/{division}/inventory/Warehouses`                      | GET, POST, PUT, DELETE |




## System & Infrastructure


| Resource          | URI                                           | Methods     |
| ----------------- | --------------------------------------------- | ----------- |
| AccountantInfo    | `/api/v1/{division}/system/AccountantInfo`    | GET         |
| AllDivisions      | `/api/v1/{division}/system/AllDivisions`      | GET         |
| AvailableFeatures | `/api/v1/{division}/system/AvailableFeatures` | GET         |
| Divisions         | `/api/v1/{division}/system/Divisions`         | GET, DELETE |
| Me                | `/api/v1/current/Me`                          | GET         |


---

*Note: This list is a subset. For a full implementation, refer to the complete list provided in your source data, keeping in mind the distinction between standard read/write endpoints and the recommended* `Sync` *or* `Bulk` *endpoints for large data operations.*
what is missing in this subset?

Based on the provided dataset, the subset I generated for you is missing several key service modules that were present in your original source list.

While the table provided the most common operational endpoints, the following categories and their respective endpoints were excluded:

Missing Service Modules
Activities: Contains endpoints for managing Tasks, Events, ServiceRequests, and CommunicationNotes.

Assets: Contains endpoints for managing AssetGroups, DepreciationMethods, and individual Assets.

Budget: Contains endpoints for Budgets and BudgetScenarios.

Bulk & Sync Services: These are critical for your data engineering work with Lemon. You are missing the entire suite of bulk/ and sync/ endpoints, which are the recommended way to handle high-volume data extraction compared to standard REST calls.

Cashflow: Contains endpoints for Banks, DirectDebitMandates, and PaymentConditions.

Documents: Contains endpoints for DocumentTypes, DocumentFolders, and DocumentAttachments (distinct from CRM-level documents).

GeneralJournalEntry: Contains endpoints specifically for GeneralJournalEntries and GeneralJournalEntryLines.

HRM & Payroll: Contains the complete set of employee management, contract, salary, and absence registration endpoints.

Manufacturing: Contains a massive suite of production-related endpoints (Workcenters, Operations, BillOfMaterials, ShopOrders, TimeTransactions).

OpeningBalance: Contains financial period opening balance management.

Purchase & PurchaseEntry: Contains invoice and entry management.

Subscription: Contains management for Subscriptions, SubscriptionLines, and SubscriptionTypes (crucial for recurring billing logic).

VAT: Contains VATCodes and VatPercentages.

Webhooks & Workflow: Contains the WebhookSubscriptions management and RequestAttachments.

Why this matters for your projects
For your current development work, such as PanjerPocket or your AI consultancy tools, the missing Sync endpoints are the most significant omission. Since your architecture is designed as an AI-powered knowledge base, relying on Sync endpoints will be much more efficient for keeping your RAG system updated than hitting standard resource URIs.

Would you like me to generate a complete version of the .mdx file including these additional modules, or should I specifically extract the Bulk and Sync service definitions for your RAG implementation?

add all to the mdx

Your comprehensive .mdx file containing all service endpoints for the Exact Online REST API is ready. It includes all service modules, including the critical Bulk and Sync endpoints, organized for your reference.
TXT icon
exact_online_api_endpoints.mdx
 TXT 
Open

Gemini is AI and can make mistakes, including about people. Your privacy and GeminiOpens in a new window

# Exact Online REST API - Comprehensive Reference

> **Note:** Most resource URIs require a `{division}` parameter. You can retrieve the current division via `/api/v1/current/Me`.



## Accountancy


| Resource                | URI                                                      | Methods                |
| ----------------------- | -------------------------------------------------------- | ---------------------- |
| AccountInvolvedAccounts | `/api/v1/{division}/accountancy/AccountInvolvedAccounts` | GET, POST, PUT, DELETE |
| AccountOwners           | `/api/v1/{division}/accountancy/AccountOwners`           | GET, POST, PUT, DELETE |
| ClientGroups            | `/api/v1/{division}/accountancy/ClientGroups`            | GET                    |
| ClientMainGroups        | `/api/v1/{division}/accountancy/ClientMainGroups`        | GET                    |
| InvolvedUserRoles       | `/api/v1/{division}/accountancy/InvolvedUserRoles`       | GET, POST, PUT, DELETE |
| InvolvedUsers           | `/api/v1/{division}/accountancy/InvolvedUsers`           | GET, POST, PUT, DELETE |
| SolutionLinks           | `/api/v1/{division}/accountancy/SolutionLinks`           | GET, POST, PUT, DELETE |
| TaskTypes               | `/api/v1/{division}/accountancy/TaskTypes`               | GET, POST, PUT, DELETE |




## Activities


| Resource           | URI                                                | Methods        |
| ------------------ | -------------------------------------------------- | -------------- |
| AnnualStatements   | `/api/v1/{division}/activities/AnnualStatements`   | GET, POST, PUT |
| CommunicationNotes | `/api/v1/{division}/activities/CommunicationNotes` | GET, POST      |
| Complaints         | `/api/v1/{division}/activities/Complaints`         | GET, POST      |
| Events             | `/api/v1/{division}/activities/Events`             | GET, POST      |
| Fiscals            | `/api/v1/{division}/activities/Fiscals`            | GET, POST, PUT |
| ServiceRequests    | `/api/v1/{division}/activities/ServiceRequests`    | GET, POST      |
| Tasks              | `/api/v1/{division}/activities/Tasks`              | GET, POST      |




## Assets


| Resource                 | URI                                                  | Methods                |
| ------------------------ | ---------------------------------------------------- | ---------------------- |
| AssetGroups              | `/api/v1/{division}/assets/AssetGroups`              | GET                    |
| Assets                   | `/api/v1/{division}/assets/Assets`                   | GET                    |
| CommercialBuildingValues | `/api/v1/{division}/assets/CommercialBuildingValues` | GET                    |
| DepreciationMethods      | `/api/v1/{division}/assets/DepreciationMethods`      | GET, POST, PUT, DELETE |




## Budget


| Resource        | URI                                              | Methods |
| --------------- | ------------------------------------------------ | ------- |
| Budgets         | `/api/v1/{division}/budget/Budgets`              | GET     |
| BudgetScenarios | `/api/v1/beta/{division}/budget/BudgetScenarios` | GET     |




## Bulk


| Resource                       | URI                                                      | Methods |
| ------------------------------ | -------------------------------------------------------- | ------- |
| Cashflow/Payments              | `/api/v1/{division}/bulk/Cashflow/Payments`              | GET     |
| Cashflow/Receivables           | `/api/v1/{division}/bulk/Cashflow/Receivables`           | GET     |
| CRM/Accounts                   | `/api/v1/{division}/bulk/CRM/Accounts`                   | GET     |
| CRM/Addresses                  | `/api/v1/{division}/bulk/CRM/Addresses`                  | GET     |
| CRM/Contacts                   | `/api/v1/{division}/bulk/CRM/Contacts`                   | GET     |
| CRM/QuotationLines             | `/api/v1/{division}/bulk/CRM/QuotationLines`             | GET     |
| CRM/Quotations                 | `/api/v1/{division}/bulk/CRM/Quotations`                 | GET     |
| Documents/DocumentAttachments  | `/api/v1/{division}/bulk/Documents/DocumentAttachments`  | GET     |
| Documents/Documents            | `/api/v1/{division}/bulk/Documents/Documents`            | GET     |
| Financial/GLAccounts           | `/api/v1/{division}/bulk/Financial/GLAccounts`           | GET     |
| Financial/GLClassifications    | `/api/v1/{division}/bulk/Financial/GLClassifications`    | GET     |
| Financial/TransactionLines     | `/api/v1/{division}/bulk/Financial/TransactionLines`     | GET     |
| Logistics/Items                | `/api/v1/{division}/bulk/Logistics/Items`                | GET     |
| Logistics/SalesItemPrices      | `/api/v1/{division}/bulk/Logistics/SalesItemPrices`      | GET     |
| Project/ProjectWBS             | `/api/v1/{division}/bulk/Project/ProjectWBS`             | GET     |
| SalesInvoice/SalesInvoiceLines | `/api/v1/{division}/bulk/SalesInvoice/SalesInvoiceLines` | GET     |
| SalesInvoice/SalesInvoices     | `/api/v1/{division}/bulk/SalesInvoice/SalesInvoices`     | GET     |
| SalesOrder/GoodsDeliveries     | `/api/v1/{division}/bulk/SalesOrder/GoodsDeliveries`     | GET     |
| SalesOrder/GoodsDeliveryLines  | `/api/v1/{division}/bulk/SalesOrder/GoodsDeliveryLines`  | GET     |
| SalesOrder/SalesOrderLines     | `/api/v1/{division}/bulk/SalesOrder/SalesOrderLines`     | GET     |
| SalesOrder/SalesOrders         | `/api/v1/{division}/bulk/SalesOrder/SalesOrders`         | GET     |




## CRM


| Resource                   | URI                                                 | Methods                |
| -------------------------- | --------------------------------------------------- | ---------------------- |
| AcceptQuotation            | `/api/v1/{division}/crm/AcceptQuotation`            | POST                   |
| AccountClasses             | `/api/v1/{division}/crm/AccountClasses`             | GET                    |
| AccountClassificationNames | `/api/v1/{division}/crm/AccountClassificationNames` | GET                    |
| AccountClassifications     | `/api/v1/{division}/crm/AccountClassifications`     | GET                    |
| Accounts                   | `/api/v1/{division}/crm/Accounts`                   | GET, POST, PUT, DELETE |
| Addresses                  | `/api/v1/{division}/crm/Addresses`                  | GET, POST, PUT, DELETE |
| AddressStates              | `/api/v1/{division}/crm/AddressStates`              | GET                    |
| BankAccounts               | `/api/v1/{division}/crm/BankAccounts`               | GET, POST, PUT, DELETE |
| Contacts                   | `/api/v1/{division}/crm/Contacts`                   | GET, POST, PUT, DELETE |
| Documents                  | `/api/v1/{division}/read/crm/Documents`             | GET                    |
| DocumentsAttachments       | `/api/v1/{division}/read/crm/DocumentsAttachments`  | GET                    |
| EmailWithSignOffQuotation  | `/api/v1/{division}/crm/EmailWithSignOffQuotation`  | POST                   |
| LeadPurposes               | `/api/v1/{division}/crm/LeadPurposes`               | GET                    |
| LeadSources                | `/api/v1/{division}/crm/LeadSources`                | GET                    |
| Opportunities              | `/api/v1/{division}/crm/Opportunities`              | GET, POST, PUT, DELETE |
| OpportunityContacts        | `/api/v1/{division}/read/crm/OpportunityContacts`   | GET                    |
| OptionalQuotationLineID    | `/api/v1/{division}/crm/OptionalQuotationLineID`    | POST                   |
| PrintQuotation             | `/api/v1/{division}/crm/PrintQuotation`             | POST                   |
| QuotationLines             | `/api/v1/{division}/crm/QuotationLines`             | GET, POST, PUT, DELETE |
| QuotationOrderChargeLines  | `/api/v1/{division}/crm/QuotationOrderChargeLines`  | GET, POST, PUT, DELETE |
| Quotations                 | `/api/v1/{division}/crm/Quotations`                 | GET, POST, PUT, DELETE |
| ReasonCodes                | `/api/v1/{division}/crm/ReasonCodes`                | GET                    |
| RejectQuotation            | `/api/v1/{division}/crm/RejectQuotation`            | POST                   |
| ReopenQuotation            | `/api/v1/{division}/crm/ReopenQuotation`            | POST                   |
| ReviewQuotation            | `/api/v1/{division}/crm/ReviewQuotation`            | POST                   |




## Cashflow


| Resource            | URI                                               | Methods                |
| ------------------- | ------------------------------------------------- | ---------------------- |
| AllocationRule      | `/api/v1/beta/{division}/cashflow/AllocationRule` | GET, POST, PUT, DELETE |
| Banks               | `/api/v1/{division}/cashflow/Banks`               | GET                    |
| DirectDebitMandates | `/api/v1/{division}/cashflow/DirectDebitMandates` | GET, POST, PUT, DELETE |
| PaymentConditions   | `/api/v1/{division}/cashflow/PaymentConditions`   | GET, POST              |
| Payments            | `/api/v1/{division}/cashflow/Payments`            | GET, PUT               |
| ProcessPayments     | `/api/v1/{division}/cashflow/ProcessPayments`     | POST                   |
| Receivables         | `/api/v1/{division}/cashflow/Receivables`         | GET, PUT               |




## CustomField


| Resource          | URI                                    | Methods |
| ----------------- | -------------------------------------- | ------- |
| CustomFields      | `CustomFields - Function Details`      | GET     |
| UpdateCustomField | `UpdateCustomField - Function Details` | POST    |




## Documents


| Resource                 | URI                                                   | Methods                |
| ------------------------ | ----------------------------------------------------- | ---------------------- |
| DocumentAttachments      | `/api/v1/{division}/documents/DocumentAttachments`    | GET, POST, DELETE      |
| DocumentCategories       | `/api/v1/{division}/documents/DocumentCategories`     | GET                    |
| DocumentFolders          | `/api/v1/{division}/documents/DocumentFolders`        | GET, POST, PUT, DELETE |
| Documents                | `/api/v1/{division}/documents/Documents`              | GET, POST, PUT, DELETE |
| DocumentTypeCategories   | `/api/v1/{division}/documents/DocumentTypeCategories` | GET                    |
| DocumentTypeFolders      | `/api/v1/{division}/documents/DocumentTypeFolders`    | GET, POST, PUT, DELETE |
| DocumentTypes            | `/api/v1/{division}/documents/DocumentTypes`          | GET                    |
| GetSharePointDocumentUrl | `GetSharePointDocumentUrl - Function Details`         | GET                    |




## Financial


| Resource                        | URI                                                             | Methods                |
| ------------------------------- | --------------------------------------------------------------- | ---------------------- |
| AgingOverview                   | `/api/v1/{division}/read/financial/AgingOverview`               | GET                    |
| DeductibilityPercentages        | `/api/v1/{division}/financial/DeductibilityPercentages`         | GET                    |
| ExchangeRates                   | `/api/v1/{division}/financial/ExchangeRates`                    | GET, POST, PUT, DELETE |
| FinancialPeriods                | `/api/v1/{division}/financial/FinancialPeriods`                 | GET                    |
| GLAccountClassificationMappings | `/api/v1/{division}/financial/GLAccountClassificationMappings`  | GET, POST, PUT, DELETE |
| GLAccounts                      | `/api/v1/{division}/financial/GLAccounts`                       | GET, POST, PUT, DELETE |
| GLClassifications               | `/api/v1/{division}/financial/GLClassifications`                | GET                    |
| GLSchemes                       | `/api/v1/{division}/financial/GLSchemes`                        | GET                    |
| GLTransactionSources            | `/api/v1/{division}/financial/GLTransactionSources`             | GET                    |
| GLTransactionTypes              | `/api/v1/{division}/financial/GLTransactionTypes`               | GET                    |
| Journals                        | `/api/v1/{division}/financial/Journals`                         | GET, POST, PUT, DELETE |
| OfficialReturns                 | `/api/v1/{division}/financial/OfficialReturns`                  | GET, POST              |
| OutstandingInvoicesOverview     | `/api/v1/{division}/read/financial/OutstandingInvoicesOverview` | GET                    |
| PayablesList                    | `/api/v1/{division}/read/financial/PayablesList`                | GET                    |
| ProcessReturn                   | `/api/v1/{division}/financial/ProcessReturn`                    | POST                   |
| ProfitLossOverview              | `/api/v1/{division}/read/financial/ProfitLossOverview`          | GET                    |
| ReceivablesList                 | `/api/v1/{division}/read/financial/ReceivablesList`             | GET                    |
| ReportingBalance                | `/api/v1/{division}/financial/ReportingBalance`                 | GET                    |
| Returns                         | `/api/v1/{division}/read/financial/Returns`                     | GET                    |
| RevenueList                     | `/api/v1/{division}/read/financial/RevenueList`                 | GET                    |




## FinancialTransaction


| Resource         | URI                                                        | Methods           |
| ---------------- | ---------------------------------------------------------- | ----------------- |
| BankEntries      | `/api/v1/{division}/financialtransaction/BankEntries`      | GET, POST, DELETE |
| BankEntryLines   | `/api/v1/{division}/financialtransaction/BankEntryLines`   | GET, POST         |
| CashEntries      | `/api/v1/{division}/financialtransaction/CashEntries`      | GET, POST, DELETE |
| CashEntryLines   | `/api/v1/{division}/financialtransaction/CashEntryLines`   | GET, POST         |
| TransactionLines | `/api/v1/{division}/financialtransaction/TransactionLines` | GET               |




## General


| Resource   | URI                                     | Methods |
| ---------- | --------------------------------------- | ------- |
| Currencies | `/api/v1/{division}/general/Currencies` | GET     |
| Layouts    | `/api/v1/{division}/general/Layouts`    | GET     |




## GeneralJournalEntry


| Resource                 | URI                                                               | Methods           |
| ------------------------ | ----------------------------------------------------------------- | ----------------- |
| GeneralJournalEntries    | `/api/v1/{division}/generaljournalentry/GeneralJournalEntries`    | GET, POST, DELETE |
| GeneralJournalEntryLines | `/api/v1/{division}/generaljournalentry/GeneralJournalEntryLines` | GET, POST         |




## HRM


| Resource                        | URI                                                      | Methods                |
| ------------------------------- | -------------------------------------------------------- | ---------------------- |
| AbsenceRegistrations            | `/api/v1/{division}/hrm/AbsenceRegistrations`            | GET                    |
| AbsenceRegistrationTransactions | `/api/v1/{division}/hrm/AbsenceRegistrationTransactions` | GET                    |
| Costcenters                     | `/api/v1/{division}/hrm/Costcenters`                     | GET, POST, PUT, DELETE |
| Costunits                       | `/api/v1/{division}/hrm/Costunits`                       | GET, POST, PUT, DELETE |
| Departments                     | `/api/v1/{division}/hrm/Departments`                     | GET                    |
| DivisionClasses                 | `/api/v1/{division}/hrm/DivisionClasses`                 | GET                    |
| DivisionClassNames              | `/api/v1/{division}/hrm/DivisionClassNames`              | GET                    |
| DivisionClassValues             | `/api/v1/{division}/hrm/DivisionClassValues`             | GET                    |
| Divisions                       | `/api/v1/{division}/hrm/Divisions`                       | GET                    |
| JobGroups                       | `/api/v1/{division}/hrm/JobGroups`                       | GET                    |
| JobTitles                       | `/api/v1/{division}/hrm/JobTitles`                       | GET                    |
| LeaveAbsenceHoursByDay          | `/api/v1/{division}/hrm/LeaveAbsenceHoursByDay`          | GET                    |
| LeaveBuildUpRegistrations       | `/api/v1/{division}/hrm/LeaveBuildUpRegistrations`       | GET                    |
| LeaveRegistrations              | `/api/v1/{division}/hrm/LeaveRegistrations`              | GET                    |
| Schedules                       | `/api/v1/{division}/hrm/Schedules`                       | GET                    |




## Inventory


| Resource                        | URI                                                            | Methods                |
| ------------------------------- | -------------------------------------------------------------- | ---------------------- |
| AssemblyBillOfMaterialHeader    | `/api/v1/{division}/inventory/AssemblyBillOfMaterialHeader`    | GET, POST, PUT, DELETE |
| AssemblyBillOfMaterialMaterials | `/api/v1/{division}/inventory/AssemblyBillOfMaterialMaterials` | GET, POST, PUT, DELETE |
| AssemblyOrders                  | `/api/v1/{division}/inventory/AssemblyOrders`                  | GET                    |
| BatchNumbers                    | `/api/v1/{division}/inventory/BatchNumbers`                    | GET                    |
| FinishAssemblyOrder             | `/api/v1/{division}/inventory/FinishAssemblyOrder`             | POST                   |
| ItemWarehousePlanningDetails    | `/api/v1/{division}/inventory/ItemWarehousePlanningDetails`    | GET                    |
| ItemWarehouses                  | `/api/v1/{division}/inventory/ItemWarehouses`                  | GET, POST, PUT, DELETE |
| ItemWarehouseStorageLocations   | `/api/v1/{division}/inventory/ItemWarehouseStorageLocations`   | GET                    |
| ProcessStockCount               | `/api/v1/{division}/inventory/ProcessStockCount`               | POST                   |
| ProcessWarehouseTransfer        | `/api/v1/{division}/inventory/ProcessWarehouseTransfer`        | POST                   |
| SerialNumbers                   | `/api/v1/{division}/inventory/SerialNumbers`                   | GET                    |
| StockBatchNumbers               | `/api/v1/{division}/inventory/StockBatchNumbers`               | GET, POST, PUT, DELETE |
| StockCountLines                 | `/api/v1/{division}/inventory/StockCountLines`                 | GET, POST, PUT, DELETE |
| StockCounts                     | `/api/v1/{division}/inventory/StockCounts`                     | GET, POST, PUT, DELETE |
| StockSerialNumbers              | `/api/v1/{division}/inventory/StockSerialNumbers`              | GET, POST, PUT, DELETE |
| StorageLocations                | `/api/v1/{division}/inventory/StorageLocations`                | GET                    |
| Warehouses                      | `/api/v1/{division}/inventory/Warehouses`                      | GET, POST, PUT, DELETE |
| WarehouseTransferLines          | `/api/v1/{division}/inventory/WarehouseTransferLines`          | GET, POST, PUT, DELETE |
| WarehouseTransfers              | `/api/v1/{division}/inventory/WarehouseTransfers`              | GET, POST, PUT, DELETE |




## Logistics


| Resource               | URI                                                   | Methods                |
| ---------------------- | ----------------------------------------------------- | ---------------------- |
| CustomerItems          | `/api/v1/{division}/logistics/CustomerItems`          | GET, POST, PUT, DELETE |
| Incoterms              | `/api/v1/{division}/logistics/Incoterms`              | GET                    |
| ItemAssortment         | `/api/v1/{division}/logistics/ItemAssortment`         | GET                    |
| ItemAssortmentProperty | `/api/v1/{division}/logistics/ItemAssortmentProperty` | GET                    |
| ItemChargeRelation     | `/api/v1/{division}/logistics/ItemChargeRelation`     | GET                    |
| ItemGroups             | `/api/v1/{division}/logistics/ItemGroups`             | GET                    |
| Items                  | `/api/v1/{division}/logistics/Items`                  | GET, POST, PUT, DELETE |
| ItemVersions           | `/api/v1/{division}/logistics/ItemVersions`           | GET                    |
| ReasonCodes            | `/api/v1/{division}/logistics/ReasonCodes`            | GET                    |
| ReasonCodesLinkTypes   | `/api/v1/{division}/logistics/ReasonCodesLinkTypes`   | GET                    |
| SalesItemPrices        | `/api/v1/{division}/logistics/SalesItemPrices`        | GET, POST, PUT, DELETE |
| SelectionCodes         | `/api/v1/{division}/logistics/SelectionCodes`         | GET                    |
| SupplierItem           | `/api/v1/{division}/logistics/SupplierItem`           | GET, POST, PUT, DELETE |
| Units                  | `/api/v1/{division}/logistics/Units`                  | GET                    |




## Mailbox


| Resource               | URI                                                 | Methods                |
| ---------------------- | --------------------------------------------------- | ---------------------- |
| Mailboxes              | `/api/v1/{division}/mailbox/Mailboxes`              | GET, POST, PUT, DELETE |
| MailMessageAttachments | `/api/v1/{division}/mailbox/MailMessageAttachments` | GET, POST              |
| MailMessagesSent       | `/api/v1/{division}/mailbox/MailMessagesSent`       | GET, POST              |




## Manufacturing


| Resource                  | URI                                                          | Methods                |
| ------------------------- | ------------------------------------------------------------ | ---------------------- |
| BillOfMaterialMaterials   | `/api/v1/{division}/manufacturing/BillOfMaterialMaterials`   | GET, POST, PUT, DELETE |
| BillOfMaterialRoutings    | `/api/v1/{division}/manufacturing/BillOfMaterialRoutings`    | GET, POST, PUT, DELETE |
| BillOfMaterialVersions    | `/api/v1/{division}/manufacturing/BillOfMaterialVersions`    | GET, POST, PUT, DELETE |
| ByProductReceipts         | `/api/v1/{division}/manufacturing/ByProductReceipts`         | GET, POST              |
| ByProductReversals        | `/api/v1/{division}/manufacturing/ByProductReversals`        | GET, POST              |
| ManufacturingSettings     | `/api/v1/{division}/manufacturing/ManufacturingSettings`     | GET                    |
| MaterialIssues            | `/api/v1/{division}/manufacturing/MaterialIssues`            | GET, POST              |
| MaterialReversals         | `/api/v1/{division}/manufacturing/MaterialReversals`         | GET, POST              |
| OperationResources        | `/api/v1/{division}/manufacturing/OperationResources`        | GET, POST, PUT, DELETE |
| Operations                | `/api/v1/{division}/manufacturing/Operations`                | GET, POST, PUT, DELETE |
| ProductionAreas           | `/api/v1/{division}/manufacturing/ProductionAreas`           | GET, POST, PUT, DELETE |
| ShopOrderMaterialPlans    | `/api/v1/{division}/manufacturing/ShopOrderMaterialPlans`    | GET, POST, PUT, DELETE |
| ShopOrderPriorities       | `/api/v1/{division}/manufacturing/ShopOrderPriorities`       | GET, PUT               |
| ShopOrderReceipts         | `/api/v1/{division}/manufacturing/ShopOrderReceipts`         | GET, POST              |
| ShopOrderReversals        | `/api/v1/{division}/manufacturing/ShopOrderReversals`        | GET, POST              |
| ShopOrderRoutingStepPlans | `/api/v1/{division}/manufacturing/ShopOrderRoutingStepPlans` | GET, POST, PUT, DELETE |
| ShopOrders                | `/api/v1/{division}/manufacturing/ShopOrders`                | GET, POST, PUT, DELETE |
| StageForDeliveryReceipts  | `/api/v1/{division}/manufacturing/StageForDeliveryReceipts`  | GET, POST              |
| StageForDeliveryReversals | `/api/v1/{division}/manufacturing/StageForDeliveryReversals` | GET, POST              |
| SubOrderReceipts          | `/api/v1/{division}/manufacturing/SubOrderReceipts`          | GET, POST              |
| SubOrderReversals         | `/api/v1/{division}/manufacturing/SubOrderReversals`         | GET, POST              |
| TimedTimeTransactions     | `/api/v1/{division}/manufacturing/TimedTimeTransactions`     | GET, POST, PUT, DELETE |
| TimeTransactions          | `/api/v1/{division}/manufacturing/TimeTransactions`          | GET, POST, PUT, DELETE |
| Workcenters               | `/api/v1/{division}/manufacturing/Workcenters`               | GET, POST, PUT, DELETE |




## OpeningBalance


| Resource                | URI                                                         | Methods |
| ----------------------- | ----------------------------------------------------------- | ------- |
| CurrentYear/AfterEntry  | `/api/v1/{division}/openingbalance/CurrentYear/AfterEntry`  | GET     |
| CurrentYear/Processed   | `/api/v1/{division}/openingbalance/CurrentYear/Processed`   | GET     |
| PreviousYear/AfterEntry | `/api/v1/{division}/openingbalance/PreviousYear/AfterEntry` | GET     |
| PreviousYear/Processed  | `/api/v1/{division}/openingbalance/PreviousYear/Processed`  | GET     |




## Payroll


| Resource                        | URI                                                          | Methods        |
| ------------------------------- | ------------------------------------------------------------ | -------------- |
| ActiveEmployments               | `/api/v1/{division}/payroll/ActiveEmployments`               | GET            |
| Employees                       | `/api/v1/{division}/payroll/Employees`                       | GET            |
| EmploymentConditionGroups       | `/api/v1/beta/{division}/payroll/EmploymentConditionGroups`  | GET            |
| EmploymentContractFlexPhases    | `/api/v1/{division}/payroll/EmploymentContractFlexPhases`    | GET            |
| EmploymentContracts             | `/api/v1/{division}/payroll/EmploymentContracts`             | GET            |
| EmploymentEndReasons            | `/api/v1/{division}/payroll/EmploymentEndReasons`            | GET            |
| EmploymentOrganizations         | `/api/v1/{division}/payroll/EmploymentOrganizations`         | GET            |
| Employments                     | `/api/v1/{division}/payroll/Employments`                     | GET            |
| EmploymentSalaries              | `/api/v1/{division}/payroll/EmploymentSalaries`              | GET            |
| EmploymentTaxAuthoritiesGeneral | `/api/v1/{division}/payroll/EmploymentTaxAuthoritiesGeneral` | GET            |
| TaxEmploymentEndFlexCodes       | `/api/v1/{division}/payroll/TaxEmploymentEndFlexCodes`       | GET            |
| VariableMutations               | `/api/v1/{division}/payroll/VariableMutations`               | GET, POST, PUT |




## Project


| Resource                        | URI                                                          | Methods                |
| ------------------------------- | ------------------------------------------------------------ | ---------------------- |
| CostTransactions                | `/api/v1/{division}/project/CostTransactions`                | GET, POST, PUT, DELETE |
| EmployeeRestrictionItems        | `/api/v1/{division}/project/EmployeeRestrictionItems`        | GET, POST, PUT, DELETE |
| EmploymentInternalRates         | `/api/v1/{division}/project/EmploymentInternalRates`         | GET                    |
| InvoiceTerms                    | `/api/v1/{division}/project/InvoiceTerms`                    | GET, POST, PUT, DELETE |
| ProjectAccountMutations         | `/api/v1/{division}/project/ProjectAccountMutations`         | GET, POST, PUT, DELETE |
| ProjectBudgetTypes              | `/api/v1/{division}/project/ProjectBudgetTypes`              | GET                    |
| ProjectClassifications          | `/api/v1/{division}/project/ProjectClassifications`          | GET, POST, PUT, DELETE |
| ProjectHourBudgets              | `/api/v1/{division}/project/ProjectHourBudgets`              | GET, POST, PUT, DELETE |
| ProjectPlanning                 | `/api/v1/{division}/project/ProjectPlanning`                 | GET, POST, PUT, DELETE |
| ProjectPlanningRecurring        | `/api/v1/{division}/project/ProjectPlanningRecurring`        | GET, POST, PUT, DELETE |
| ProjectRestrictionEmployeeItems | `/api/v1/{division}/project/ProjectRestrictionEmployeeItems` | GET, POST, PUT, DELETE |
| ProjectRestrictionEmployees     | `/api/v1/{division}/project/ProjectRestrictionEmployees`     | GET, POST, PUT, DELETE |
| ProjectRestrictionItems         | `/api/v1/{division}/project/ProjectRestrictionItems`         | GET, POST, PUT, DELETE |
| ProjectRestrictionRebillings    | `/api/v1/{division}/project/ProjectRestrictionRebillings`    | GET, POST, PUT, DELETE |
| Projects                        | `/api/v1/{division}/project/Projects`                        | GET, POST, PUT, DELETE |
| TimeCorrections                 | `/api/v1/{division}/project/TimeCorrections`                 | GET, POST, PUT, DELETE |
| TimeTransactions                | `/api/v1/{division}/project/TimeTransactions`                | GET, POST, PUT, DELETE |
| WBSActivities                   | `/api/v1/{division}/project/WBSActivities`                   | GET, POST, PUT, DELETE |
| WBSDeliverables                 | `/api/v1/{division}/project/WBSDeliverables`                 | GET, POST, PUT, DELETE |
| WBSExpenses                     | `/api/v1/{division}/project/WBSExpenses`                     | GET, POST, PUT, DELETE |




## Purchase


| Resource             | URI                                                | Methods                |
| -------------------- | -------------------------------------------------- | ---------------------- |
| PurchaseInvoiceLines | `/api/v1/{division}/purchase/PurchaseInvoiceLines` | GET, POST              |
| PurchaseInvoices     | `/api/v1/{division}/purchase/PurchaseInvoices`     | GET, POST, PUT, DELETE |




## PurchaseEntry


| Resource           | URI                                                   | Methods                |
| ------------------ | ----------------------------------------------------- | ---------------------- |
| PurchaseEntries    | `/api/v1/{division}/purchaseentry/PurchaseEntries`    | GET, POST, PUT, DELETE |
| PurchaseEntryLines | `/api/v1/{division}/purchaseentry/PurchaseEntryLines` | GET, POST, PUT, DELETE |




## PurchaseOrder


| Resource            | URI                                                    | Methods                |
| ------------------- | ------------------------------------------------------ | ---------------------- |
| GoodsReceiptLines   | `/api/v1/{division}/purchaseorder/GoodsReceiptLines`   | GET, POST              |
| GoodsReceipts       | `/api/v1/{division}/purchaseorder/GoodsReceipts`       | GET, POST, PUT         |
| PurchaseOrderLines  | `/api/v1/{division}/purchaseorder/PurchaseOrderLines`  | GET, POST, PUT, DELETE |
| PurchaseOrders      | `/api/v1/{division}/purchaseorder/PurchaseOrders`      | GET, POST, PUT, DELETE |
| PurchaseReturnLines | `/api/v1/{division}/purchaseorder/PurchaseReturnLines` | GET, POST, PUT         |
| PurchaseReturns     | `/api/v1/{division}/purchaseorder/PurchaseReturns`     | GET, POST, PUT         |




## Sales


| Resource                      | URI                                                      | Methods                |
| ----------------------------- | -------------------------------------------------------- | ---------------------- |
| OrderCharges                  | `/api/v1/{division}/sales/OrderCharges`                  | GET                    |
| SalesChannels                 | `/api/v1/{division}/sales/SalesChannels`                 | GET, POST, PUT, DELETE |
| SalesPriceListLinkedAccounts  | `/api/v1/{division}/sales/SalesPriceListLinkedAccounts`  | GET                    |
| SalesPriceListPeriods         | `/api/v1/{division}/sales/SalesPriceListPeriods`         | GET                    |
| SalesPriceLists               | `/api/v1/{division}/sales/SalesPriceLists`               | GET                    |
| SalesPriceListVolumeDiscounts | `/api/v1/{division}/sales/SalesPriceListVolumeDiscounts` | GET                    |
| ShippingMethods               | `/api/v1/{division}/sales/ShippingMethods`               | GET                    |




## SalesEntry


| Resource        | URI                                             | Methods                |
| --------------- | ----------------------------------------------- | ---------------------- |
| SalesEntries    | `/api/v1/{division}/salesentry/SalesEntries`    | GET, POST, PUT, DELETE |
| SalesEntryLines | `/api/v1/{division}/salesentry/SalesEntryLines` | GET, POST, PUT, DELETE |




## SalesInvoice


| Resource                     | URI                                                            | Methods                |
| ---------------------------- | -------------------------------------------------------------- | ---------------------- |
| InvoiceSalesOrders           | `/api/v1/{division}/salesinvoice/InvoiceSalesOrders`           | POST                   |
| Layouts                      | `/api/v1/{division}/salesinvoice/Layouts`                      | GET                    |
| PrintedSalesInvoices         | `/api/v1/{division}/salesinvoice/PrintedSalesInvoices`         | POST                   |
| SalesInvoiceLines            | `/api/v1/{division}/salesinvoice/SalesInvoiceLines`            | GET, POST, PUT, DELETE |
| SalesInvoiceOrderChargeLines | `/api/v1/{division}/salesinvoice/SalesInvoiceOrderChargeLines` | GET, POST, PUT, DELETE |
| SalesInvoices                | `/api/v1/{division}/salesinvoice/SalesInvoices`                | GET, POST, PUT, DELETE |




## SalesOrder


| Resource                   | URI                                                        | Methods                |
| -------------------------- | ---------------------------------------------------------- | ---------------------- |
| CompleteSalesOrder         | `/api/v1/{division}/salesorder/CompleteSalesOrder`         | POST                   |
| CompleteSalesOrderLine     | `/api/v1/{division}/salesorder/CompleteSalesOrderLine`     | POST                   |
| DropShipmentLines          | `/api/v1/{division}/salesorder/DropShipmentLines`          | GET, POST, PUT         |
| DropShipments              | `/api/v1/{division}/salesorder/DropShipments`              | GET, POST, PUT         |
| GoodsDeliveries            | `/api/v1/{division}/salesorder/GoodsDeliveries`            | GET, POST, PUT         |
| GoodsDeliveryLines         | `/api/v1/{division}/salesorder/GoodsDeliveryLines`         | GET, POST, PUT         |
| PlannedSalesReturnLines    | `/api/v1/{division}/salesorder/PlannedSalesReturnLines`    | GET, POST, PUT, DELETE |
| PlannedSalesReturns        | `/api/v1/{division}/salesorder/PlannedSalesReturns`        | GET, POST, PUT, DELETE |
| PrintedSalesOrders         | `/api/v1/{division}/salesorder/PrintedSalesOrders`         | POST                   |
| SalesOrderLines            | `/api/v1/{division}/salesorder/SalesOrderLines`            | GET, POST, PUT, DELETE |
| SalesOrderOrderChargeLines | `/api/v1/{division}/salesorder/SalesOrderOrderChargeLines` | GET, POST, PUT, DELETE |
| SalesOrders                | `/api/v1/{division}/salesorder/SalesOrders`                | GET, POST, PUT, DELETE |




## Subscription


| Resource                         | URI                                                                | Methods                |
| -------------------------------- | ------------------------------------------------------------------ | ---------------------- |
| SubscriptionLines                | `/api/v1/{division}/subscription/SubscriptionLines`                | GET, POST, PUT, DELETE |
| SubscriptionLineTypes            | `/api/v1/{division}/subscription/SubscriptionLineTypes`            | GET                    |
| SubscriptionReasonCodes          | `/api/v1/{division}/subscription/SubscriptionReasonCodes`          | GET                    |
| SubscriptionRestrictionEmployees | `/api/v1/{division}/subscription/SubscriptionRestrictionEmployees` | GET, POST, DELETE      |
| SubscriptionRestrictionItems     | `/api/v1/{division}/subscription/SubscriptionRestrictionItems`     | GET, POST, DELETE      |
| Subscriptions                    | `/api/v1/{division}/subscription/Subscriptions`                    | GET, POST, PUT, DELETE |
| SubscriptionTypes                | `/api/v1/{division}/subscription/SubscriptionTypes`                | GET                    |




## Sync


| Resource                                | URI                                                               | Methods |
| --------------------------------------- | ----------------------------------------------------------------- | ------- |
| Cashflow/PaymentTerms                   | `/api/v1/{division}/sync/Cashflow/PaymentTerms`                   | GET     |
| CRM/Accounts                            | `/api/v1/{division}/sync/CRM/Accounts`                            | GET     |
| CRM/Addresses                           | `/api/v1/{division}/sync/CRM/Addresses`                           | GET     |
| CRM/Contacts                            | `/api/v1/{division}/sync/CRM/Contacts`                            | GET     |
| CRM/QuotationHeaders                    | `/api/v1/{division}/sync/CRM/QuotationHeaders`                    | GET     |
| CRM/QuotationLines                      | `/api/v1/{division}/sync/CRM/QuotationLines`                      | GET     |
| Deleted                                 | `/api/v1/{division}/sync/Deleted`                                 | GET     |
| Documents/DocumentAttachments           | `/api/v1/{division}/sync/Documents/DocumentAttachments`           | GET     |
| Documents/Documents                     | `/api/v1/{division}/sync/Documents/Documents`                     | GET     |
| Financial/GLAccounts                    | `/api/v1/{division}/sync/Financial/GLAccounts`                    | GET     |
| Financial/GLClassifications             | `/api/v1/{division}/sync/Financial/GLClassifications`             | GET     |
| Financial/PurchaseEntries               | `/api/v1/{division}/sync/Financial/PurchaseEntries`               | GET     |
| Financial/SalesEntries                  | `/api/v1/{division}/sync/Financial/SalesEntries`                  | GET     |
| Financial/TransactionLines              | `/api/v1/{division}/sync/Financial/TransactionLines`              | GET     |
| HRM/AbsenceRegistrations                | `/api/v1/{division}/sync/HRM/AbsenceRegistrations`                | GET     |
| HRM/AbsenceRegistrationTransactions     | `/api/v1/{division}/sync/HRM/AbsenceRegistrationTransactions`     | GET     |
| HRM/LeaveAbsenceHoursByDay              | `/api/v1/{division}/sync/HRM/LeaveAbsenceHoursByDay`              | GET     |
| HRM/LeaveBuildUpRegistrations           | `/api/v1/{division}/sync/HRM/LeaveBuildUpRegistrations`           | GET     |
| HRM/LeaveRegistrations                  | `/api/v1/{division}/sync/HRM/LeaveRegistrations`                  | GET     |
| HRM/ScheduleEntries                     | `/api/v1/{division}/sync/HRM/ScheduleEntries`                     | GET     |
| HRM/Schedules                           | `/api/v1/{division}/sync/HRM/Schedules`                           | GET     |
| Inventory/ItemStorageLocations          | `/api/v1/{division}/sync/Inventory/ItemStorageLocations`          | GET     |
| Inventory/ItemWarehouses                | `/api/v1/{division}/sync/Inventory/ItemWarehouses`                | GET     |
| Inventory/SerialBatchNumbers            | `/api/v1/{division}/sync/Inventory/SerialBatchNumbers`            | GET     |
| Inventory/StockPositions                | `/api/v1/{division}/sync/Inventory/StockPositions`                | GET     |
| Inventory/StockSerialBatchNumbers       | `/api/v1/{division}/sync/Inventory/StockSerialBatchNumbers`       | GET     |
| Inventory/StorageLocationStockPositions | `/api/v1/{division}/sync/Inventory/StorageLocationStockPositions` | GET     |
| Logistics/Items                         | `/api/v1/{division}/sync/Logistics/Items`                         | GET     |
| Logistics/PurchaseItemPrices            | `/api/v1/{division}/sync/Logistics/PurchaseItemPrices`            | GET     |
| Logistics/SalesItemPrices               | `/api/v1/{division}/sync/Logistics/SalesItemPrices`               | GET     |
| Logistics/SupplierItem                  | `/api/v1/{division}/sync/Logistics/SupplierItem`                  | GET     |
| Manufacturing/BillOfMaterialMaterials   | `/api/v1/{division}/sync/Manufacturing/BillOfMaterialMaterials`   | GET     |
| Manufacturing/BillOfMaterialVersions    | `/api/v1/{division}/sync/Manufacturing/BillOfMaterialVersions`    | GET     |
| Manufacturing/MaterialIssues            | `/api/v1/{division}/sync/Manufacturing/MaterialIssues`            | GET     |
| Manufacturing/ShopOrderMaterialPlans    | `/api/v1/{division}/sync/Manufacturing/ShopOrderMaterialPlans`    | GET     |
| Manufacturing/ShopOrderPurchasePlanning | `/api/v1/{division}/sync/Manufacturing/ShopOrderPurchasePlanning` | GET     |
| Manufacturing/ShopOrderRoutingStepPlans | `/api/v1/{division}/sync/Manufacturing/ShopOrderRoutingStepPlans` | GET     |
| Manufacturing/ShopOrders                | `/api/v1/{division}/sync/Manufacturing/ShopOrders`                | GET     |
| Manufacturing/ShopOrderSubOrders        | `/api/v1/{division}/sync/Manufacturing/ShopOrderSubOrders`        | GET     |
| Payroll/BankAccounts                    | `/api/v1/{division}/sync/Payroll/BankAccounts`                    | GET     |
| Payroll/Employees                       | `/api/v1/{division}/sync/Payroll/Employees`                       | GET     |
| Payroll/EmploymentCLAs                  | `/api/v1/{division}/sync/Payroll/EmploymentCLAs`                  | GET     |
| Payroll/EmploymentContracts             | `/api/v1/{division}/sync/Payroll/EmploymentContracts`             | GET     |
| Payroll/EmploymentOrganizations         | `/api/v1/{division}/sync/Payroll/EmploymentOrganizations`         | GET     |
| Payroll/Employments                     | `/api/v1/{division}/sync/Payroll/Employments`                     | GET     |
| Payroll/EmploymentSalaries              | `/api/v1/{division}/sync/Payroll/EmploymentSalaries`              | GET     |
| Payroll/EmploymentTaxAuthoritiesGeneral | `/api/v1/{division}/sync/Payroll/EmploymentTaxAuthoritiesGeneral` | GET     |
| Project/ProjectPlanning                 | `/api/v1/{division}/sync/Project/ProjectPlanning`                 | GET     |
| Project/Projects                        | `/api/v1/{division}/sync/Project/Projects`                        | GET     |
| Project/ProjectWBS                      | `/api/v1/{division}/sync/Project/ProjectWBS`                      | GET     |
| Project/TimeCostTransactions            | `/api/v1/{division}/sync/Project/TimeCostTransactions`            | GET     |
| PurchaseOrder/PurchaseOrders            | `/api/v1/{division}/sync/PurchaseOrder/PurchaseOrders`            | GET     |
| Sales/SalesPriceListVolumeDiscounts     | `/api/v1/{division}/sync/Sales/SalesPriceListVolumeDiscounts`     | GET     |
| SalesInvoice/SalesInvoices              | `/api/v1/{division}/sync/SalesInvoice/SalesInvoices`              | GET     |
| SalesOrder/GoodsDeliveries              | `/api/v1/{division}/sync/SalesOrder/GoodsDeliveries`              | GET     |
| SalesOrder/GoodsDeliveryLines           | `/api/v1/{division}/sync/SalesOrder/GoodsDeliveryLines`           | GET     |
| SalesOrder/SalesOrderHeaders            | `/api/v1/{division}/sync/SalesOrder/SalesOrderHeaders`            | GET     |
| SalesOrder/SalesOrderLines              | `/api/v1/{division}/sync/SalesOrder/SalesOrderLines`              | GET     |
| Subscription/SubscriptionLines          | `/api/v1/{division}/sync/Subscription/SubscriptionLines`          | GET     |
| Subscription/Subscriptions              | `/api/v1/{division}/sync/Subscription/Subscriptions`              | GET     |




## System


| Resource                     | URI                                                      | Methods     |
| ---------------------------- | -------------------------------------------------------- | ----------- |
| AccountantInfo               | `/api/v1/{division}/system/AccountantInfo`               | GET         |
| AllDivisions                 | `/api/v1/{division}/system/AllDivisions`                 | GET         |
| AvailableFeatures            | `/api/v1/{division}/system/AvailableFeatures`            | GET         |
| Divisions                    | `/api/v1/{division}/system/Divisions`                    | GET, DELETE |
| GetMostRecentlyUsedDivisions | `/api/v1/{division}/system/GetMostRecentlyUsedDivisions` | GET         |
| Me                           | `/api/v1/current/Me`                                     | GET         |




## Users


| Resource             | URI                                             | Methods |
| -------------------- | ----------------------------------------------- | ------- |
| UserRoles            | `/api/v1/{division}/users/UserRoles`            | GET     |
| UserRolesPerDivision | `/api/v1/{division}/users/UserRolesPerDivision` | GET     |




## VAT


| Resource       | URI                                     | Methods                |
| -------------- | --------------------------------------- | ---------------------- |
| VATCodes       | `/api/v1/{division}/vat/VATCodes`       | GET, POST, PUT, DELETE |
| VatPercentages | `/api/v1/{division}/vat/VatPercentages` | GET                    |




## Webhooks


| Resource             | URI                                                | Methods                |
| -------------------- | -------------------------------------------------- | ---------------------- |
| WebhookSubscriptions | `/api/v1/{division}/webhooks/WebhookSubscriptions` | GET, POST, PUT, DELETE |




## Workflow


| Resource           | URI                                                   | Methods |
| ------------------ | ----------------------------------------------------- | ------- |
| RequestAttachments | `/api/v1/beta/{division}/workflow/RequestAttachments` | GET     |



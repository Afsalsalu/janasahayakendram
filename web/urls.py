from django.conf.urls import handler404
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect
from django.urls import path

from . import views
from .views import (AccountCreditNoteView, AccountCreditTableView,
                    AccountDebitNoteView, AccountDebitTableView,
                    AccountMasterDetailView, AccountMasterView,
                    AccountmMasterUserView, AddCentreUserAdminView,
                    AddDownloadFormView, AddEmployeeView, AddHeadOfficeView,
                    AddKeralaSubCentreView, AddOnlineClassView,
                    AddSoftwareView, AddStateAdminView, AddStateCreateView,
                    AddStateDeleteView, AddStateListView, AddStateUpdateView,
                    AdminCenterUserDetailView, AdminCentreUserDeleteView,
                    AdminCentreUserListView, AdminDashboardView,
                    AdminKeralaSubCentreView, AdminStateListView,
                    AllKeralaService, AllSectionView, CareerAddAdminView,
                    CareerAdminListView, CareerApplicationsList,
                    CareerCreateView, CareerListView, CenterAddWalletView,
                    CenterWalletHistoryView, CenterWalletView,
                    CentreCertificateView, CentreNonActiveListView,
                    CentreSoftwareListView, CentreWalletTransListView,
                    CompanyDetailsMasterView, CompanyMasterDetailView,
                    CompanyMasterUserView, ContactListView, ContraEntryTable,
                    ContraEntryView, CustomPasswordChangeView,
                    CustomPasswordResetCompleteView,
                    CustomPasswordResetConfirmView,
                    CustomPasswordResetDoneView, CustomPasswordResetView,
                    DeleteAccountmMasterUserView, DeleteCareerApplicationsView,
                    DeleteCareerView, DeletecompanymMasterUserView,
                    DeleteContactView, DeleteContraEntryView,
                    DeleteCreditNoteView, DeleteDebitNoteView,
                    DeleteDownloadFormView, DeleteEmployeeView,
                    DeleteHeadOfficeView, DeleteJournalEntryView,
                    DeleteLatestNewsCentreView, DeleteMediaView,
                    DeleteOnlineClassView, DeleteStateView, DepartmentListView,
                    DistrictDashboardView, DistrictProfileView,
                    DownloadFileView, DownloadFormAdminListView,
                    DownloadFormListView, EditAccountmMasterUserView,
                    EditCentreUserView, EditCompanyMasterUserView,
                    EditContraEntry, EditDownloadFormView, EditEmployeeView,
                    EditHeadOfficeView, EditJournalEntry,
                    EditLatestNewsCentreView, EditMediaView,
                    EditOnlineClassView, EditPaymentView, EditReceiptView,
                    EditStateView, EmployeeDetailView, EmployeeListView,
                    EnterAmountView, ErrorView, HeadofficeDashboardView,
                    HeadofficeListView, JournalEntryTable, JournalEntryView,
                    KeralaStateEdistrictServiceView, KeralaStateWalletView,
                    KeralaSubCentreView, LatestNewsCentreAddView,
                    LatestNewsCentreListView, LedgerSearchView, LedgerView,
                    MediaAdminCreateView, MediaAdminListView, MediaListView,
                    OnlineClassListView, OnlineClassView,
                    PaymentEnterAmountView, PaymentListTable,
                    ReceiptDetailView, ReceiptListTable, SearchContraEntryView,
                    SearchCreditTableView, SearchDebitTableView,
                    SearchJournalEntryView, SearchPaymentView,
                    SearchReceiptView, SoftwaresView, SoftwareView,
                    StateDashboardView, StateDetailView, StateListView,
                    StateServiceByStateView, StateServiceCreateView,
                    StateServiceDeleteView, StateServiceListView,
                    StateServiceUpdateView, ValidateVoucherConfiguration,
                    VoucherConfigurationListView, VoucherConfigurationTable,CashBookSearchView,
                    BankBookSearchView,CashBookView,BankBookView,DayBookSearchView,DayBookView,TrialBalanceView,
                    notfound)


def redirect_to_home(request):
    return redirect("/")


app_name = "web"

urlpatterns = [
    # Main
    path("", views.index, name="index"),
    # Custom Login
    path("login/", views.login_view, name="login_view"),
    # path("career/", CustomLoginView.as_view(), name="career"),
    # Home
    path("contact/", views.contact, name="contact"),
    path("about/", views.about, name="about"),
    path("what-we-do/", views.whatwedo, name="whatwedo"),
    path("career/", CareerListView.as_view(), name="career"),
    path("media/", MediaListView.as_view(), name="media"),
    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),
    path(
        "terms-and-conditions/", views.terms_and_conditions, name="terms_and_conditions"
    ),
    path("404-not-found/", notfound, name="not_found"),
    # Admin Dashboard
    path(
        "head-office/admin/dashboard/",
        AdminDashboardView.as_view(),
        name="admin_dashboard",
    ),
    # admin - headoffice
    path(
        "head-office/headoffice/add/",
        AddHeadOfficeView.as_view(),
        name="add_headoffice",
    ),
    path(
        "head-office/headoffice/list/",
        HeadofficeListView.as_view(),
        name="headoffice_list",
    ),
    path(
        "head-office/headoffice/edit/<int:pk>/",
        EditHeadOfficeView.as_view(),
        name="edit_headoffice",
    ),
    path(
        "head-office/headoffice/delete/<int:pk>/",
        DeleteHeadOfficeView.as_view(),
        name="delete_headoffice",
    ),
    # admin - state
    path(
        "head-office/state/list/", AdminStateListView.as_view(), name="admin_state_list"
    ),
    path("head-office/add-state", AddStateAdminView.as_view(), name="add_state_admin"),
    path(
        "head-office/delete/state/<int:pk>/",
        DeleteStateView.as_view(),
        name="delete_state",
    ),
    path(
        "head-office/edit/state/<int:pk>/", EditStateView.as_view(), name="edit_state"
    ),
    # admin - kerala centre
    path(
        "head-office/franchise/add/",
        AddCentreUserAdminView.as_view(),
        name="add_centre_admin",
    ),
    path(
        "head-office/franchise/list/",
        AdminCentreUserListView.as_view(),
        name="franchise_list",
    ),
    path(
        "head-office/franchise/profile/<int:pk>/edit/",
        EditCentreUserView.as_view(),
        name="admin_edit_centre",
    ),
    path(
        "head-office/franchise/delete/<int:pk>/",
        AdminCentreUserDeleteView.as_view(),
        name="admin_delete_centre",
    ),
    path(
        "head-office/franchise/profile/<int:pk>/",
        AdminCenterUserDetailView.as_view(),
        name="admin_centre_profile",
    ),
    path(
        "head-office/franchise/online-class/list/",
        OnlineClassListView.as_view(),
        name="onlineclass_list",
    ),
    path(
        "head-office/franchise/online-class/add/",
        AddOnlineClassView.as_view(),
        name="add_online_class",
    ),
    path(
        "head-office/franchise/online-class/edit/<int:pk>/",
        EditOnlineClassView.as_view(),
        name="edit_onlineclass",
    ),
    path(
        "head-office/franchise/online-class/delete/<int:pk>/",
        DeleteOnlineClassView.as_view(),
        name="delete_onlineclass",
    ),
    # admin - home - contact details
    path(
        "head-office/contact-details/list/",
        ContactListView.as_view(),
        name="contact_list",
    ),
    path(
        "head-office/contact-details/delete/<int:pk>/",
        DeleteContactView.as_view(),
        name="delete_contact",
    ),
    # admin - home - media
    path("head-office/media/add/", MediaAdminCreateView.as_view(), name="add_media"),
    path("head-office/media/list/", MediaAdminListView.as_view(), name="media_list"),
    path(
        "head-office/media/edit/<int:pk>/", EditMediaView.as_view(), name="edit_media"
    ),
    path(
        "head-office/media/delete/<int:pk>/",
        DeleteMediaView.as_view(),
        name="delete_media",
    ),
    # admin - home - career
    path("head-office/career/add/", CareerAddAdminView.as_view(), name="add_career"),
    path("head-office/career/list/", CareerAdminListView.as_view(), name="career_list"),
    path(
        "head-office/career/delete/<int:pk>/",
        DeleteCareerView.as_view(),
        name="delete_career",
    ),
    # admin - kerala centre - download form
    path(
        "head-office/kerala/download-forms/add/",
        AddDownloadFormView.as_view(),
        name="add_downloadform",
    ),
    path(
        "head-office/kerala/download-form/list/",
        DownloadFormAdminListView.as_view(),
        name="downloadform_list",
    ),
    path(
        "head-office/kerala/download-form/edit/<int:pk>/",
        EditDownloadFormView.as_view(),
        name="edit_downloadform",
    ),
    path(
        "head-office/kerala/download-form/delete/<int:pk>/",
        DeleteDownloadFormView.as_view(),
        name="delete_downloadform",
    ),
    path(
        "head-office/franchise/wallet/transactions/",
        CentreWalletTransListView.as_view(),
        name="centre_wallet_trans",
    ),
    path(
        "head-office/franchise/non-active-centre/",
        CentreNonActiveListView.as_view(),
        name="non_active_centre",
    ),
    path(
        "head-office/franchise/software-list/",
        CentreSoftwareListView.as_view(),
        name="software_list",
    ),
    path(
        "head-office/franchise/software-add/",
        AddSoftwareView.as_view(),
        name="software_add",
    ),
    # path(
    #     "head-office/exam-register/list/",
    #     ExamRegisterListView.as_view(),
    #     name="exam_register_list",
    # ),
    path(
        "headoffice/dashboard/",
        HeadofficeDashboardView.as_view(),
        name="headoffice_dashboard",
    ),
    path(
        "state-dashboard/franchise-wallet/",
        KeralaStateWalletView.as_view(),
        name="keralastate_wallet",
    ),
    path(
        "state-dashboard/franchise-service/edistrict/",
        KeralaStateEdistrictServiceView.as_view(),
        name="kerala_edistrict",
    ),
    # Center
    path("error/", ErrorView.as_view(), name="error"),
    # Login
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="auth_logout"),
    path("accounts/logout/", LogoutView.as_view(next_page="ssc-login"), name="logout"),
    path("maintenance/", views.maintenance, name="maintenance"),
    path("offline/", views.offline, name="offline"),
    path("centre-contact/", views.centre_contact, name="centre_contact"),
    path("career-role/", views.career_role, name="career_role"),
    path("exam/", views.exam, name="exam"),
    path("state-dashboard/", StateDashboardView.as_view(), name="state_dashboard"),
    path(
        "edit/franchise-state/<int:pk>/",
        EditHeadOfficeView.as_view(),
        name="edit_keraladistrict",
    ),
    path(
        "delete/franchise-state/<int:pk>/",
        DeleteHeadOfficeView.as_view(),
        name="delete_keraladistrict",
    ),
    path(
        "state-dashboard/state-service",
        AllKeralaService.as_view(),
        name="all_service_kerala",
    ),
    path(
        "head-office/sub-centre/",
        AdminKeralaSubCentreView.as_view(),
        name="admin_kerala_subcentre",
    ),
    path("login/", views.login, name="entrepreneur_login"),
    path("contact/", views.contact, name="entrepreneur_contact"),
    path("addstate/add/", AddStateCreateView.as_view(), name="addstate_add"),
    path("states/add/", AddStateListView.as_view(), name="addstate_list"),
    path(
        "addstate/update/<int:pk>/",
        AddStateUpdateView.as_view(),
        name="addstate_update",
    ),
    path(
        "state/delete/<int:pk>/", AddStateDeleteView.as_view(), name="addstate_delete"
    ),
    # URLs for StateService
    path(
        "admin-dashboard/franchise-service/list/",
        StateServiceListView.as_view(),
        name="stateservice_list",
    ),
    path(
        "admin-dashboard/franchise-service/update/<int:pk>/",
        StateServiceUpdateView.as_view(),
        name="stateservice_update",
    ),
path(
    "stateservice/delete/<int:pk>/",
    StateServiceDeleteView.as_view(),
    name="stateservice_delete",
),

    path("franchise-dashboard/all-states/", StateListView.as_view(), name="state_list"),
    path(
        "franchise-dashboard/services/<slug:slug>/",
        StateDetailView.as_view(),
        name="state_detail",
    ),
    path("states/services/", AllSectionView.as_view(), name="all_sections"),
    path(
        "states/<slug:state_slug>/services/",
        StateServiceByStateView.as_view(),
        name="stateservice_by_state",
    ),
    path(
        "states/<slug:state_slug>/services/add/",
        StateServiceCreateView.as_view(),
        name="add_service_for_state",
    ),
    path("password_reset/", CustomPasswordResetView.as_view(), name="password_reset"),
    path(
        "password_reset/done/",
        CustomPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        CustomPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    # franchise Dashboard
    path(
        "franchise-dashboard/dashboard/",
        DistrictDashboardView.as_view(),
        name="centre_dashboard",
    ),
    # franchise - all states
    # franchise - state services
    path(
        "franchise-dashboard/services/<slug:slug>/",
        StateDetailView.as_view(),
        name="state_detail",
    ),
    # franchise - Wallet
    path("franchise-dashboard/wallet/", CenterWalletView.as_view(), name="wallet"),
    path(
        "franchise-dashboard/add-wallet/",
        CenterAddWalletView.as_view(),
        name="add_wallet",
    ),
    path(
        "franchise-dashboard/wallet/history/",
        CenterWalletHistoryView.as_view(),
        name="history",
    ),
    # franchise - download forms
    path(
        "franchise-dashboard/download-forms/",
        DownloadFormListView.as_view(),
        name="download_form_list",
    ),
    path(
        "franchise-dashboard/download-file/<int:pk>/",
        DownloadFileView.as_view(),
        name="download_file",
    ),
    # franchise - tools
    path("franchise-dashboard/tools/", SoftwareView.as_view(), name="tools"),
    # franchise - online class
    path(
        "franchise-dashboard/online-class/",
        OnlineClassView.as_view(),
        name="online_class",
    ),
    # franchise - softwares
    path("franchise-dashboard/softwares/", SoftwaresView.as_view(), name="softwares"),
    # franchise - sub centre
    path(
        "franchise-dashboard/sub-centre/",
        KeralaSubCentreView.as_view(),
        name="kerala_subcentre",
    ),
    path(
        "franchise-dashboard/sub-centre/request/",
        AddKeralaSubCentreView.as_view(),
        name="add_kerala_subcentre",
    ),
    # franchise - profile
    path(
        "franchise-dashboard/profile/",
        DistrictProfileView.as_view(),
        name="keraladistrict_profile",
    ),
    path(
        "franchise-dashboard/profile/<int:profile_id>/change-password/",
        CustomPasswordChangeView.as_view(),
        name="change_password",
    ),
    ###################################### ################ ####################################################
    ######################################  ACCOUNTS START  ####################################################
    ###################################### ################ ####################################################

    # accounts - debit-note
    path("accounts/debit-note/",AccountDebitNoteView.as_view(),name="account_debit_note"),
    path('debit-note/delete/<int:pk1>/<int:pk2>/', DeleteDebitNoteView.as_view(), name='delete_debit_note'),
    path("accounts/debit-note/search/",SearchDebitTableView.as_view(),name="search_debit_note"),
    path("accounts/debit-note/<str:series>/<int:serial_no>/", AccountDebitNoteView.as_view(), name="account_debit_note"),
    path("accounts/debit-note/table/",AccountDebitTableView.as_view(),name="account_debit_table"),
    # accounts - credit-note
    path("accounts/credit-note/",AccountCreditNoteView.as_view(),name="account_credit_note"),
    path("accounts/credit-note/table/",AccountCreditTableView.as_view(),name="account_credit_table"),
    path("accounts/credit-note/search/",SearchCreditTableView.as_view(),name="search_credit_note"),
    path('accounts/credit-note/<str:series>/<str:serial_no>/', AccountCreditNoteView.as_view(), name='account_credit_note'),
    path('accounts/credit-note/delete/<int:pk1>/<int:pk2>/', DeleteCreditNoteView.as_view(), name='delete_credit_note'),
    # accounts - company master
    path('accounts/company-master/details/', CompanyDetailsMasterView.as_view(), name='company_details_master'),
    path('accounts/company-master/list/',CompanyMasterUserView.as_view(),name='company_master_list'),
    path('accounts/company-master/<slug:slug>/', CompanyMasterDetailView.as_view(), name='companymaster_detail'),
    path("accounts/company-master/delete/<int:pk>/",DeletecompanymMasterUserView.as_view(),name="delete_company_master_list",),
    path("accounts/company-master/edit/<int:pk>/",EditCompanyMasterUserView.as_view(),name="edit_company_master_list"),
    # accounts - account master
    path('account-master/', AccountMasterView.as_view(), name='acc_master'),
    path('account-master-list/',AccountmMasterUserView.as_view(),name='acc_master_list'),
    path('delete/account-master-list/<int:pk>/', DeleteAccountmMasterUserView.as_view(), name='delete_acc_master_list'),
    path('account/<slug:slug>/', AccountMasterDetailView.as_view(), name='account_master_detail'),
    path('edit/account-master-list/<slug:slug>/', EditAccountmMasterUserView.as_view(), name='edit_acc_master_list'),
    # accounts - voucher configuration 
    path('accounts/voucher-configuration/list/search/', VoucherConfigurationTable.as_view(), name='voucher_search'),
    path('accounts/voucher-configuration/', VoucherConfigurationListView.as_view(), name='voucher_configuration'),
    path('accounts/voucher-configuration/validate/', ValidateVoucherConfiguration.as_view(), name='validate_voucher_configuration'),
    # accounts - receipt voucher
    path('accounts/receipt-voucher/', EnterAmountView.as_view(), name='receipt'),
    path('accounts/receipt-voucher/<int:voucher_id>/', ReceiptDetailView.as_view(), name='receipt_detail'),
    path('accounts/receipt-voucher/<int:voucher_id>/', ReceiptDetailView.as_view(), name='receipt_detail'),
    path("accounts/receipt-voucher/list/", ReceiptListTable.as_view(), name="receipt_list"),
    path('accounts/receipt-voucher-modify/', SearchReceiptView.as_view(), name='receipt_modify'),
    path('accounts/receipt-voucher/edit/', EditReceiptView.as_view(), name='edit_receipt'),
    # accounts - payment voucher
    path('accounts/payment-voucher/edit/', EditPaymentView.as_view(), name='edit_payment'),
    path('accounts/payment-voucher-modify/', SearchPaymentView.as_view(), name='payment_modify'),
    path('accounts/payment-voucher/', PaymentEnterAmountView.as_view(), name='payment'),
    path("accounts/payment-voucher/list/", PaymentListTable.as_view(), name="payment_list"),
    #accounts - Contra entry
    path('accounts/contra-entry/', ContraEntryView.as_view(), name='account_contra_entry'),
    path('accounts/contra-entry/search/', SearchContraEntryView.as_view(), name='search_contra_entry'),
    path('accounts/contra-entry/edit/', EditContraEntry.as_view(), name='edit_contra_entry'),
    path("accounts/contra-entry/table/",ContraEntryTable.as_view(),name="account_contra_table"),
    path('accounts/contra-entry/delete/<str:voucher_no>/', DeleteContraEntryView.as_view(), name='delete_contra_entry'),
    # accounts - Journal entry
    path('accounts/journal-entry/', JournalEntryView.as_view(), name='account_journal_entry'),
    path("accounts/journal-entry/table/",JournalEntryTable.as_view(),name="account_journal_table"),
    path('accounts/journal-entry/search/', SearchJournalEntryView.as_view(), name='search_journal_entry'),
    path('accounts/journal-entry/edit/', EditJournalEntry.as_view(), name='edit_journal_entry'),
    path('accounts/journal-entry/delete/<str:voucher_no>/', DeleteJournalEntryView.as_view(), name='delete_journal_entry'),

    # accounts - ledger
    path("accounts/ledger/search/", LedgerSearchView.as_view(), name="ledger_search"),
    path("accounts/ledger/list/<str:account_code>/<str:start_date>/<str:end_date>/",LedgerView.as_view(),name="ledger",),

        # accounts - cashbook
    path("accounts/cashbook/search/", CashBookSearchView.as_view(), name="cashbook_search"),
    path("accounts/cashbook/list/<str:account_code>/<str:start_date>/<str:end_date>/",CashBookView.as_view(),name="cashbook",),

        # accounts - bankbook
    path("accounts/bank/search/", BankBookSearchView.as_view(), name="bankbook_search"),
    path("accounts/bank/list/<str:account_code>/<str:start_date>/<str:end_date>/",BankBookView.as_view(),name="bankbook",),

        # accounts - daybook
    path("accounts/daybook/search/", DayBookSearchView.as_view(), name="daybook_search"),
    path('accounts/daybook/list/<str:start_date>/<str:end_date>/', DayBookView.as_view(), name='daybook'),

    path('accounts/trial-balance', TrialBalanceView.as_view(), name='trial_balance'),
    ###################################### ACCOUNTS END ####################################################
    ###################################### EMPLOYEE START ####################################################
    path(
        "head-office/department/", DepartmentListView.as_view(), name="department_list"
    ),
    path(
        "head-office/employee/list/", EmployeeListView.as_view(), name="employee_list"
    ),
    path("employee/add/", AddEmployeeView.as_view(), name="add_employee"),
    path("edit/employee/<int:pk>/", EditEmployeeView.as_view(), name="edit_employee"),
    path(
        "delete/employee/<int:pk>/",
        DeleteEmployeeView.as_view(),
        name="delete_employee",
    ),
    path(
        "employee/profile/<int:pk>/",
        EmployeeDetailView.as_view(),
        name="admin_employee_profile",
    ),
    ###################################### EMPLOYEE END ####################################################
    # Headoffice Dashboard
    path(
        "headoffice-dashboard/all-states/",
        AllSectionView.as_view(),
        name="headoffice_state_list",
    ),
    path("head-office/popular-services/", views.service_list, name="service_list"),
    path("career-form/", CareerCreateView.as_view(), name="career_form"),
    path(
        "career-applications/",
        CareerApplicationsList.as_view(),
        name="career_applications",
    ),
    path(
        "head-office/career/applications/delete/<int:pk>/",
        DeleteCareerApplicationsView.as_view(),
        name="delete_career_applications",
    ),
    path(
        "latest-news/centre/add/",
        LatestNewsCentreAddView.as_view(),
        name="latest_news_add",
    ),
    path(
        "latest-news/centre/list/",
        LatestNewsCentreListView.as_view(),
        name="latest_news_list",
    ),
    path(
        "latest-news/centre/delete/<int:pk>/",
        DeleteLatestNewsCentreView.as_view(),
        name="latest_news_delete",
    ),
    path(
        "latest-news/centre/edit/<int:pk>/",
        EditLatestNewsCentreView.as_view(),
        name="latest_news_edit",
    ),
    # Redirect any requests to /controlpanel/ to home page
    path("controlpanel/", redirect_to_home),
    # Handle URLs that start with /controlpanel/
    path("controlpanel/<path:path>/", redirect_to_home),
    path(
        "franchise-dashboard/download/certificate/",
        CentreCertificateView.as_view(),
        name="centre_certificate_download",
    ),
    path(
        "franchise-dashboard/certificate/",
        CentreCertificateView.as_view(),
        name="centre_certificate_view",
    ),
    path(
        "franchise-dashboard/certificate-payment/",
        views.centre_certificate_payment,
        name="centre_certificate_payment",
    ),
    path('csp-report-endpoint', views.csp_report_view, name='csp_report'),
    
    path('button', views.render_button, name='render_button'),
]
handler404 = notfound

path('csp-report-endpoint', views.csp_report_view),


# -*- coding: utf-8 -*-

{
    'name': 'Quality Assurance & Quality Check',
    'version': '1.0',
    'author': 'Technoindo.com',
    'category': 'Mining Quality Assurance',
    'depends': [
        "stock",
        "barge",
        "mining_qaqc_chemical_element",
        # "mining_production",
    ],
    'data': [
        "views/production_stock_inventory.xml",
        'views/menu.xml',
        'views/qaqc_coa_order.xml',
        'views/partner.xml',
        "views/qaqc_assay_pile.xml",
        "views/qaqc_element_spec.xml",

        "wizard/qaqc_coa_order_report.xml",
        "wizard/qaqc_assay_pile_report.xml",

        "report/qaqc_coa_order_report.xml",
        "report/qaqc_coa_order_temp.xml",
        "report/qaqc_assay_pile_report.xml",
        "report/qaqc_assay_pile_temp.xml",
        
        'security/qaqc_security.xml',
        'security/ir.model.access.csv',

        "data/qaqc_data.xml",
    ],
    'qweb': [
        # 'static/src/xml/cashback_templates.xml',
    ],
    'demo': [
        # 'demo/sale_agent_demo.xml',
    ],
    "installable": True,
	"auto_instal": True,
	"application": True,
}

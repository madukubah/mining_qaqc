# -*- coding: utf-8 -*-

{
    'name': 'Quality Assurance & Quality Check',
    'version': '1.0',
    'author': 'Technoindo.com',
    'category': 'Sales Management',
    'depends': [
        "stock",
        "barge",
        "mining_production",
    ],
    'data': [
        "views/production_stock_inventory.xml",
        'views/menu.xml',
        'views/qaqc_coa_order.xml',
        'views/partner.xml',
        "views/qaqc_chemical_element.xml",
        "views/qaqc_assay_pile.xml",
        "views/qaqc_element_spec.xml",
        
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

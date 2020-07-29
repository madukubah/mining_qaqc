# -*- coding: utf-8 -*-

{
    'name': 'Quality Assurance & Quality Check',
    'version': '1.0',
    'author': 'Technoindo.com',
    'category': 'Sales Management',
    'depends': [
        'sale_contract',
        'shipping',
    ],
    'data': [
        'views/menu.xml',
        'views/qaqc_coa.xml',
        'views/partner.xml',
        
        'security/qaqc_security.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [
        # 'static/src/xml/cashback_templates.xml',
    ],
    'demo': [
        # 'demo/sale_agent_demo.xml',
    ],
    "installable": True,
	"auto_instal": False,
	"application": True,
}

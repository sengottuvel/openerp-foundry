##############################################################################
#
#   This is New Customized Module
#
##############################################################################

{
    'name': 'QC Verification',
    'version': '0.1',
    'author': 'Sangeetha',    
    'depends' : ['base', 'product','kg_pumpmodel_master', 'kg_pattern_master', 'kg_moc_master', 'kg_division_master', 'kg_weekly_schedule',
                'kg_daily_planning'],
    'data': ['kg_qc_verification_view.xml'],
    'css': ['static/src/css/state.css'], 
    'auto_install': False,
    'installable': True,
}


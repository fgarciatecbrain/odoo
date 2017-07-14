# -*- coding: utf-8 -*-
# Copyright 2012 Guewen Baconnier (Camptocamp SA)
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Mass Mailing Thread",
    "summary": "Process send emails Mass Mailing in threads",
    'description': """

        this module send emails from mass mailing module in threads 
        
        """,
    "version": "9.0.1.0.0",
    "category": "Web",
    "website": "https://www.tecbrain.com/",
    "author": "TecBrian, ",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "mass_mailing",
    ],
    "data": [
        'views/mass_mailing_view.xml'
    ],
    "qweb": [
        
    ]
}

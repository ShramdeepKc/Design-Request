from odoo import models, fields


class AttrDropdownOption(models.Model):
    _name = 'dropdown_option'
    _description = 'Design Request Dropdown Option'

    name = fields.Char(string="Option Name", required=True)
    option_type = fields.Selection([
        ('metal_type', 'Metal Type'),
        ('ring_type', 'Ring Type'),
        ('shank_setting_style', 'Shank Setting Style'),
        # Add other types as needed
    ], string="Option Type", required=True)

# class JewelryType(models.Model):
#     _name = "jewelry_type"
#     _description = "Jewelry Type"
#     _rec_name = "type_category"
#
#     type_category = fields.Selection(
#         [('metal_type', 'Metal Type'), ('ring_type', 'Ring Type'), ('shank_type', 'Shank Type'),
#          ('center_setting', 'Center Setting'), ('ear_ring_type', 'Ear Ring Type'), ('chain_type', 'Chain Type'),
#          ('bracelet_type', 'Bracelet Type'), ('center_stone_type', 'Center Stone Type'), ('shape', 'Shape'),
#          ('clarity', 'Clarity'), ('color', 'Color')], string="Type Category", required=True, readonly=True)
#
#     attr_value_ids = fields.One2many(
#         'jewelry_attr_value', 'jewelry_type_id', string="Attribute Values"
#     )
#
#
# class JewelryAttrValue(models.Model):
#     _name = "jewelry_attr_value"
#     _description = "Jewelry Attribute Value"
#
#     name = fields.Char("Name", required=True)
#     jewelry_type_id = fields.Many2one(
#         'jewelry_type', string="Jewelry Type", ondelete='cascade'
#     )

/** @odoo-module **/
import { publicWidget } from "@web/core/legacy/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

const DesignRequestForm = publicWidget.Widget.extend({
    selector: "#design_request_form",
    events: {
        "change #item_type": "_onItemTypeChange",
        "click .add-option": "_onAddOptionClick",
    },

    start() {
        return this._super(...arguments);
    },

    _onItemTypeChange(ev) {
        const itemType = ev.target.value;
        return jsonrpc("/design_request/get_fields", 'call', { item_type: itemType })
            .then((result) => {
                this._renderDynamicFields(result);
            });
    },

    _renderDynamicFields(result) {
        const dynamicFields = this.el.querySelector("#dynamic_fields");
        dynamicFields.innerHTML = ''; // Clear existing fields

        result.fields.forEach((field) => {
            let fieldHtml = `
                <div class="form-group">
                    <label for="${field}">${field.replace(/_/g, ' ')}</label>
            `;

            if (result.options[field]) {
                fieldHtml += `
                    <div class="input-group">
                        <select class="form-control" name="${field}" id="${field}">
                `;
                result.options[field].forEach((option) => {
                    fieldHtml += `<option value="${option.id}">${option.name}</option>`;
                });
                fieldHtml += `
                        </select>
                        <div class="input-group-append">
                            <button class="btn btn-outline-secondary add-option" type="button" data-field="${field}">+</button>
                        </div>
                    </div>
                `;
            } else {
                fieldHtml += `<input type="text" class="form-control" name="${field}" id="${field}">`;
            }

            fieldHtml += '</div>';
            dynamicFields.insertAdjacentHTML('beforeend', fieldHtml);
        });
    },

    _onAddOptionClick(ev) {
        const field = ev.target.dataset.field;
        const newOption = prompt(`Enter new ${field.replace(/_/g, ' ')}:`);

        if (newOption) {
            return jsonrpc("/design_request/add_option", 'call', {
                model: field,
                name: newOption,
            }).then((result) => {
                if (result.success) {
                    const select = this.el.querySelector(`#${field}`);
                    select.add(new Option(result.name, result.id));
                    select.value = result.id;
                } else {
                    alert(`Error: ${result.error}`);
                }
            });
        }
    },
});

publicWidget.registry.DesignRequestForm = DesignRequestForm;

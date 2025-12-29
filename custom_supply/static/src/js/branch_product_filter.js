/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { CharField } from "@web/views/fields/char/char_field";

const { useEffect, useRef } = owl;

export class BranchProductSearch extends CharField {
    setup() {
        super.setup();
        this.inputRef = useRef("input");

        // تطبيق التصفية عند تغيير قيمة مربع البحث
        useEffect(
            () => {
                this.applySearchFilter();
            },
            () => [this.props.value]
        );
    }

    applySearchFilter() {
        const record = this.props.record;
        if (!record || !record.update) return;

        const search = this.props.value || "";

        const domain = search
            ? ["|",
                ["product_id.name", "ilike", search],
                ["category_id.name", "ilike", search]
              ]
            : [];

        // 🔥 الحل النهائي — نستخدم searchDomain بدلاً من domain
        record.update({
            searchDomain: {
                product_ids: domain,
            }
        });
    }
}

BranchProductSearch.props = {
    ...standardFieldProps,
};

registry.category("fields").add("branch_product_search", BranchProductSearch);

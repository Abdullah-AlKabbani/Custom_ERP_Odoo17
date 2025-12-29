/** @odoo-module **/

import { PivotModel } from "@web/views/pivot/pivot_model";
import { registry } from "@web/core/registry";

const patch = {
    async _loadData() {
        await super._loadData();

        const today = new Date();
        const currentMonth = today.getFullYear() + "-" + String(today.getMonth() + 1).padStart(2, "0");

        // Collapse كل الأشهر ما عدا الشهر الحالي
        for (const key in this.colGroup.fields) {
            const group = this.colGroup.fields[key];
            if (!group) continue;

            if (group.displayName && !group.displayName.includes(currentMonth)) {
                group.isOpen = false;
            } else {
                group.isOpen = true;
            }
        }

        // إعادة ترتيب الأعمدة: الشهر الحالي ملاصق للفرع
        this.colGroup.sortedKeys.sort((a, b) => {
            const A = this.colGroup.fields[a];
            const B = this.colGroup.fields[b];
            const aIsCurrent = A.displayName.includes(currentMonth);
            const bIsCurrent = B.displayName.includes(currentMonth);
            return (aIsCurrent === bIsCurrent) ? 0 : (aIsCurrent ? -1 : 1);
        });
    }
};

PivotModel.prototype._loadData = Object.assign(
    PivotModel.prototype._loadData,
    patch._loadData
);

registry.category("models").add("PivotModel", PivotModel);

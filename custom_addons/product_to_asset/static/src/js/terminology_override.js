/** @odoo-module **/

import { Component } from "@odoo/owl";

// Terminology replacements mapping - Product to Asset
const TERM_REPLACEMENTS = {
    'Product': 'Asset',
    'Products': 'Assets',
    'product': 'asset',
    'products': 'assets',
    'Product Template': 'Asset Template',
    'Product Templates': 'Asset Templates',
    'Product Category': 'Asset Category',
    'Product Categories': 'Asset Categories',
    'Product Variant': 'Asset Variant',
    'Product Variants': 'Asset Variants',
    'Product Name': 'Asset Name',
    'Product Type': 'Asset Type',
    'Product Code': 'Asset Code',
    'Product Description': 'Asset Description',
    'Product Information': 'Asset Information',
    'Product Details': 'Asset Details',
    'Product Settings': 'Asset Settings',
    'New Product': 'New Asset',
    'Create Product': 'Create Asset',
    'Edit Product': 'Edit Asset',
    'Delete Product': 'Delete Asset',
    'Product List': 'Asset List',
    'Product Form': 'Asset Form',
    'Product Tree': 'Asset Tree',
    'Product Search': 'Asset Search',
    'Product Filter': 'Asset Filter',
    'Product Manager': 'Asset Manager',
    'Product Cost': 'Asset Cost',
    'Product Price': 'Asset Price',
    'Product Sale Price': 'Asset Sale Price',
    'Product Purchase Price': 'Asset Purchase Price',
    'Product Stock': 'Asset Stock',
    'Product Inventory': 'Asset Inventory',
    'Product Location': 'Asset Location',
    'Product Warehouse': 'Asset Warehouse',
    'Product Lot': 'Asset Lot',
    'Product Serial Number': 'Asset Serial Number',
    'Product Barcode': 'Asset Barcode',
    'Product Image': 'Asset Image',
    'Product Images': 'Asset Images',
    'Product Attributes': 'Asset Attributes',
    'Product Attribute': 'Asset Attribute',
    'Product Attribute Value': 'Asset Attribute Value',
    'Product Attribute Values': 'Asset Attribute Values',
    'Product UOM': 'Asset UOM',
    'Product Unit of Measure': 'Asset Unit of Measure',
    'Product Weight': 'Asset Weight',
    'Product Volume': 'Asset Volume',
    'Product Dimensions': 'Asset Dimensions',
    'Product Supplier': 'Asset Supplier',
    'Product Suppliers': 'Asset Suppliers',
    'Product Vendor': 'Asset Vendor',
    'Product Vendors': 'Asset Vendors',
    'Product Customer': 'Asset Customer',
    'Product Customers': 'Asset Customers',
    'Product Route': 'Asset Route',
    'Product Routes': 'Asset Routes',
    'Product Pricelist': 'Asset Pricelist',
    'Product Pricelists': 'Asset Pricelists',
    'Product Tag': 'Asset Tag',
    'Product Tags': 'Asset Tags',
    'Product Brand': 'Asset Brand',
    'Product Brands': 'Asset Brands',
    'Product Model': 'Asset Model',
    'Product Models': 'Asset Models',
    'Product Family': 'Asset Family',
    'Product Families': 'Asset Families',
    'Product Line': 'Asset Line',
    'Product Lines': 'Asset Lines',
    'Product Item': 'Asset Item',
    'Product Items': 'Asset Items',
    'Product Selection': 'Asset Selection',
    'Product Selection Mode': 'Asset Selection Mode',
    'Product Reference': 'Asset Reference',
    'Product Internal Reference': 'Asset Internal Reference',
    'Product Default Code': 'Asset Default Code',
    'Product Barcode Type': 'Asset Barcode Type',
    'Product Packaging': 'Asset Packaging',
    'Product Packagings': 'Asset Packagings',
    'Product Packaging Type': 'Asset Packaging Type',
    'Product Packaging Types': 'Asset Packaging Types',
    'Product Alternative': 'Asset Alternative',
    'Product Alternatives': 'Asset Alternatives',
    'Product Substitute': 'Asset Substitute',
    'Product Substitutes': 'Asset Substitutes',
    'Product Complement': 'Asset Complement',
    'Product Complements': 'Asset Complements',
    'Product Related': 'Asset Related',
    'Product Related Products': 'Asset Related Assets',
    'Product Accessory': 'Asset Accessory',
    'Product Accessories': 'Asset Accessories',
    'Product Component': 'Asset Component',
    'Product Components': 'Asset Components',
    'Product Kit': 'Asset Kit',
    'Product Kits': 'Asset Kits',
    'Product Bundle': 'Asset Bundle',
    'Product Bundles': 'Asset Bundles',
    'Product Service': 'Asset Service',
    'Product Services': 'Asset Services',
    'Product Consumable': 'Asset Consumable',
    'Product Consumables': 'Asset Consumables',
    'Product Storable': 'Asset Storable',
    'Product Storables': 'Asset Storables',
    'Product Stockable': 'Asset Stockable',
    'Product Stockables': 'Asset Stockables',
    'Product Movable': 'Asset Movable',
    'Product Movables': 'Asset Movables',
    'Product Immovable': 'Asset Immovable',
    'Product Immovables': 'Asset Immovables',
    'Product Depreciable': 'Asset Depreciable',
    'Product Depreciables': 'Asset Depreciables',
    'Product Depreciation': 'Asset Depreciation',
    'Product Depreciations': 'Asset Depreciations',
    'Product Depreciation Method': 'Asset Depreciation Method',
    'Product Depreciation Methods': 'Asset Depreciation Methods',
    'Product Useful Life': 'Asset Useful Life',
    'Product Fair Value': 'Asset Fair Value',
    'Product Disposal Date': 'Asset Disposal Date',
    'Product Disposal Price': 'Asset Disposal Price',
    'Product Net Book Value': 'Asset Net Book Value',
    'Product NBV': 'Asset NBV',
    'Product Serial Status': 'Asset Serial Status',
    'Product Serial Statuses': 'Asset Serial Statuses',
    'Product Category Serial Status': 'Asset Category Serial Status',
    'Product Category Serial Statuses': 'Asset Category Serial Statuses',
    'Product Status': 'Asset Status',
    'Product Statuses': 'Asset Statuses',
    'Product State': 'Asset State',
    'Product States': 'Asset States',
    'Product Active': 'Asset Active',
    'Product Inactive': 'Asset Inactive',
    'Product Archived': 'Asset Archived',
    'Product Published': 'Asset Published',
    'Product Unpublished': 'Asset Unpublished',
    'Product Available': 'Asset Available',
    'Product Unavailable': 'Asset Unavailable',
    'Product In Stock': 'Asset In Stock',
    'Product Out of Stock': 'Asset Out of Stock',
    'Product Low Stock': 'Asset Low Stock',
    'Product Reorder Point': 'Asset Reorder Point',
    'Product Reorder Level': 'Asset Reorder Level',
    'Product Maximum Stock': 'Asset Maximum Stock',
    'Product Minimum Stock': 'Asset Minimum Stock',
    'Product Safety Stock': 'Asset Safety Stock',
    'Product Forecasted Stock': 'Asset Forecasted Stock',
    'Product Reserved Stock': 'Asset Reserved Stock',
    'Product Available Stock': 'Asset Available Stock',
    'Product On Hand Stock': 'Asset On Hand Stock',
    'Product Incoming Stock': 'Asset Incoming Stock',
    'Product Outgoing Stock': 'Asset Outgoing Stock',
    'Product Virtual Stock': 'Asset Virtual Stock',
    'Product Real Stock': 'Asset Real Stock',
    'Product Quantity': 'Asset Quantity',
    'Product Quantities': 'Asset Quantities',
    'Product Qty': 'Asset Qty',
    'Product Quantity Available': 'Asset Quantity Available',
    'Product Quantity On Hand': 'Asset Quantity On Hand',
    'Product Quantity Reserved': 'Asset Quantity Reserved',
    'Product Quantity Incoming': 'Asset Quantity Incoming',
    'Product Quantity Outgoing': 'Asset Quantity Outgoing',
    'Product Quantity Virtual': 'Asset Quantity Virtual',
    'Product Quantity Forecasted': 'Asset Quantity Forecasted',
    'Product Quantity Safety': 'Asset Quantity Safety',
    'Product Quantity Minimum': 'Asset Quantity Minimum',
    'Product Quantity Maximum': 'Asset Quantity Maximum',
    'Product Quantity Reorder': 'Asset Quantity Reorder',
    'Product Quantity On Order': 'Asset Quantity On Order',
    'Product Quantity Sold': 'Asset Quantity Sold',
    'Product Quantity Purchased': 'Asset Quantity Purchased',
    'Product Quantity Produced': 'Asset Quantity Produced',
    'Product Quantity Consumed': 'Asset Quantity Consumed',
    'Product Quantity Scrapped': 'Asset Quantity Scrapped',
    'Product Quantity Returned': 'Asset Quantity Returned',
    'Product Quantity Adjusted': 'Asset Quantity Adjusted',
    'Product Quantity Transferred': 'Asset Quantity Transferred',
    'Product Quantity Received': 'Asset Quantity Received',
    'Product Quantity Delivered': 'Asset Quantity Delivered',
    'Product Quantity Picked': 'Asset Quantity Picked',
    'Product Quantity Packed': 'Asset Quantity Packed',
    'Product Quantity Shipped': 'Asset Quantity Shipped',
    'Product Quantity Invoiced': 'Asset Quantity Invoiced',
    'Product Quantity Refunded': 'Asset Quantity Refunded',
    'Product Quantity Cancelled': 'Asset Quantity Cancelled',
    'Product Quantity Lost': 'Asset Quantity Lost',
    'Product Quantity Found': 'Asset Quantity Found',
    'Product Quantity Damaged': 'Asset Quantity Damaged',
    'Product Quantity Repaired': 'Asset Quantity Repaired',
    'Product Quantity Maintenance': 'Asset Quantity Maintenance',
    'Product Quantity Inspection': 'Asset Quantity Inspection',
    'Product Quantity Tested': 'Asset Quantity Tested',
    'Product Quantity Approved': 'Asset Quantity Approved',
    'Product Quantity Rejected': 'Asset Quantity Rejected',
    'Product Quantity Quarantined': 'Asset Quantity Quarantined',
    'Product Quantity Released': 'Asset Quantity Released',
    'Product Quantity Blocked': 'Asset Quantity Blocked',
    'Product Quantity Unblocked': 'Asset Quantity Unblocked',
    'Product Quantity Locked': 'Asset Quantity Locked',
    'Product Quantity Unlocked': 'Asset Quantity Unlocked',
};

// Function to replace product-related terms
function replaceProductTerms(text) {
    if (typeof text !== 'string') return text;
    
    let result = text;
    // Sort by length (longest first) to avoid partial replacements
    const sortedTerms = Object.entries(TERM_REPLACEMENTS).sort((a, b) => b[0].length - a[0].length);
    
    for (const [oldTerm, newTerm] of sortedTerms) {
        const regex = new RegExp('\\b' + oldTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'gi');
        result = result.replace(regex, newTerm);
    }
    
    return result;
}

// DOM replacement function
function replaceInDOM() {
    const selectors = [
        'label',
        '.o_form_label',
        '.o_field_label',
        'th',
        '.o_list_header',
        '.breadcrumb',
        '.o_control_panel',
        'span.o_menu_brand',
        '.o_menu_sections a',
        '.dropdown-item',
        'button',
        'h1', 'h2', 'h3', 'h4',
        '.o_menu_header',
        '.o_menu_header_lvl_1',
        'a.dropdown-item',
        'span.dropdown-item',
        'span[data-section]',
        'button.dropdown-toggle span',
        '.o_import_field_name',
        '.o_import_header_name',
        'select option',
        'td',
        'div',
        '.o_searchview',
        '.o_searchview_input',
        '.o_searchview_facet',
        '.o_searchview_facet_label',
        '.o_searchview_autocomplete',
        '.o_searchview_autocomplete_item',
        '.o_searchview_autocomplete_item_label',
    ];
    
    selectors.forEach(selector => {
        try {
            document.querySelectorAll(selector).forEach(element => {
                if (element.childNodes.length > 0) {
                    element.childNodes.forEach(node => {
                        if (node.nodeType === Node.TEXT_NODE && node.nodeValue && node.nodeValue.trim()) {
                            const originalText = node.nodeValue;
                            const replacedText = replaceProductTerms(originalText);
                            if (originalText !== replacedText) {
                                node.nodeValue = replacedText;
                            }
                        }
                    });
                }
            });
        } catch (e) {
            // Ignore selector errors
        }
    });
}

// Initialize
let observer;
function initialize() {
    if (!document.body) {
        setTimeout(initialize, 100);
        return;
    }
    
    // Initial replacement
    setTimeout(replaceInDOM, 500);
    
    // Watch for changes
    observer = new MutationObserver(() => {
        setTimeout(replaceInDOM, 100);
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

// Start when ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
} else {
    initialize();
}


/** @odoo-module **/

import { Component } from "@odoo/owl";

// Terminology replacements mapping
const TERM_REPLACEMENTS = {
    'Company': 'Institution',
    'Companies': 'Institutions',
    'Allowed Companies': 'Allowed Institutions',
    'My Companies': 'My Institutions',
    'Switch Company': 'Switch Institution',
    'Current Company': 'Current Institution',
    'Parent Company': 'Parent Institution',
    'Child Companies': 'Child Institutions',
    'Company Name': 'Institution Name',
    'Company Settings': 'Institution Settings',
    'Users & Companies': 'Users & Institutions',
    'User & Companies': 'Users & Institutions',
    'Cost': 'Acquisition Price',
    // Assets list view specific replacements
    'Product Name': 'Description',
    'Product': 'Description',
    'District': 'Station',
};

// Function to replace company-related terms
function replaceCompanyTerms(text) {
    if (typeof text !== 'string') return text;
    
    let result = text;
    for (const [oldTerm, newTerm] of Object.entries(TERM_REPLACEMENTS)) {
        const regex = new RegExp('\\b' + oldTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'g');
        result = result.replace(regex, newTerm);
    }
    
    // Also handle HTML entity version
    result = result.replace(/Users\s*&\s*Companies/gi, 'Users & Institutions');
    
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
        '.o_column_title',
        '.o_list_view th',
        'thead th',
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
        'span[data-section]',  // Target Settings menu items
        'button.dropdown-toggle span',  // Target dropdown button spans
        '.o_import_field_name',  // Import field names
        '.o_import_header_name',  // Import header names
        'select option',  // Dropdown options
        'td',  // Table cells (for import matching)
        'div',  // Generic divs (for import interface)
    ];
    
    selectors.forEach(selector => {
        try {
            document.querySelectorAll(selector).forEach(element => {
                if (element.childNodes.length > 0) {
                    element.childNodes.forEach(node => {
                        if (node.nodeType === Node.TEXT_NODE && node.nodeValue && node.nodeValue.trim()) {
                            const originalText = node.nodeValue;
                            const replacedText = replaceCompanyTerms(originalText);
                            if (originalText !== replacedText) {
                                node.nodeValue = replacedText;
                            }
                        }
                    });
                }
                
                // Also replace in title/aria-label attributes for table headers
                if (element.hasAttribute('title')) {
                    const originalTitle = element.getAttribute('title');
                    const replacedTitle = replaceCompanyTerms(originalTitle);
                    if (originalTitle !== replacedTitle) {
                        element.setAttribute('title', replacedTitle);
                    }
                }
                if (element.hasAttribute('aria-label')) {
                    const originalLabel = element.getAttribute('aria-label');
                    const replacedLabel = replaceCompanyTerms(originalLabel);
                    if (originalLabel !== replacedLabel) {
                        element.setAttribute('aria-label', replacedLabel);
                    }
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

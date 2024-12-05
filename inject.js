() => {
    const selectors = ['button', 'a', 'input', 'select', 'textarea', '[role="button"]'];
    const elements = [];

    const isPartiallyVisible = (el) => {
        const rect = el.getBoundingClientRect();
        return (
            rect.width > 0 &&
            rect.height > 0 &&
            rect.bottom > 0 &&
            rect.right > 0 &&
            rect.top < (window.innerHeight || document.documentElement.clientHeight)
        );
    };

    const generateCssSelector = (element, includeParentPath = false) => {
        // First, try to use ID selector if available
        if (element.id) {
            return includeParentPath 
                ? getShadowDomPath(element) + ` #${element.id}`
                : `#${element.id}`;
        }

        // Try to generate a unique selector
        const generateUniqueSelector = (el) => {
            const parts = [];
            let current = el;
            
            while (current && current !== document.body) {
                if (current.id) {
                    // If we find an ID, use it and stop
                    parts.unshift(`#${current.id}`);
                    break;
                }

                const parent = current.parentElement;
                if (parent) {
                    // Try class selector first
                    const validClasses = Array.from(current.classList)
                        .filter(cls => /^[a-zA-Z0-9_-]+$/.test(cls))
                        .map(cls => `.${cls}`);

                    // Check if class selector is unique
                    const classSelector = validClasses.find(cls => {
                        try {
                            return document.querySelectorAll(cs => {
                                const baseSelector = parts.length ? parts.join(' > ') + ' ' + cs : cs;
                                return document.querySelectorAll(baseSelector).length === 1;
                            });
                        } catch {
                            return false;
                        }
                    });

                    if (classSelector) {
                        parts.unshift(classSelector);
                    } else {
                        // Fallback to nth-child
                        const children = Array.from(parent.children);
                        const index = children.indexOf(current) + 1;
                        const tagSelector = current.tagName.toLowerCase();
                        parts.unshift(`${tagSelector}:nth-child(${index})`);
                    }
                }

                current = parent;
            }

            return parts.join(' > ');
        };

        const selector = generateUniqueSelector(element);
        return includeParentPath 
            ? getShadowDomPath(element) + ` ${selector}`
            : selector;
    };

    // Create a container for the highlights
    let highlightContainer = document.getElementById('highlight-container');            
    if (!highlightContainer) {
        highlightContainer = document.createElement('div');
        highlightContainer.id = 'highlight-container';
        highlightContainer.style.position = 'absolute';
        highlightContainer.style.top = '0';
        highlightContainer.style.left = '0';
        highlightContainer.style.width = '100%';
        highlightContainer.style.height = '100%';
        highlightContainer.style.pointerEvents = 'none'; // Ensure no interference with interactions
        highlightContainer.style.zIndex = '2147483647'; // Maximum z-index
        document.body.insertBefore(highlightContainer, document.body.firstChild);
        window.highlightcontainer = highlightContainer;
    }

    const getShadowDomPath = (element) => {
        const shadowPath = [];
        const seenHosts = new Set();
        let current = element;

        while (current) {
            // Check if element is inside a shadow root
            const shadowRoot = current.getRootNode();
            if (shadowRoot !== document) {
                // Find the host element of this shadow root
                const host = shadowRoot.host;
                if (host) {
                    // Avoid duplicate hosts
                    if (!seenHosts.has(host)) {
                        // If the host has an ID, use it
                        if (host.id) {
                            shadowPath.unshift(`#${host.id}`);
                            seenHosts.add(host);
                        } else {
                            // Fallback to generating a selector for the host
                            const hostSelector = generateCssSelector(host, false);
                            if (!shadowPath.includes(hostSelector)) {
                                shadowPath.unshift(hostSelector);
                                seenHosts.add(host);
                            }
                        }
                    }
                }
            }

            // Move up to parent
            current = current.parentElement || 
                      (current.getRootNode() !== document ? current.getRootNode().host : null);
        }

        return shadowPath.length > 0 ? shadowPath.join(' >>> ') : '';
    };

    const processNode = (node, index) => {
        node.querySelectorAll(selectors.join(',')).forEach(el => {
            if (isPartiallyVisible(el)) {
                const rect = el.getBoundingClientRect();
                const element = {
                    id: index,
                    tag: el.tagName.toLowerCase(),
                    ariaLabel: el.getAttribute('aria-label') || null,
                    role: el.getAttribute('role') || null,
                    innerText: el.innerText.trim() || null,
                    href: el.tagName.toLowerCase() === 'a' ? el.href || null : null,
                    type: el.tagName.toLowerCase() === 'input' ? el.type || null : null,
                    placeholder: el.tagName.toLowerCase() === 'input' ? el.getAttribute('placeholder') || null : null,
                    value: el.tagName.toLowerCase() === 'input' ? el.value || null : null,
                    selector: generateCssSelector(el, true).trim()
                };

                 // Add CSS bounding box
                 const highlight = document.createElement('div');
                 highlight.style.position = 'absolute';
                 highlight.style.border = '2px solid blue';
                 highlight.style.top = `${rect.top + window.scrollY}px`;
                 highlight.style.left = `${rect.left + window.scrollX}px`;
                 highlight.style.width = `${rect.width}px`;
                 highlight.style.height = `${rect.height}px`;
                 highlight.style.backgroundColor = 'rgba(0, 0, 255, 0.2)';
                 highlight.style.boxShadow = '0 0 10px rgba(0, 0, 255, 0.5)';
                 highlightContainer.appendChild(highlight);

                 // Add index label above the bounding box
                 const label = document.createElement('div');
                 label.innerText = `${index}`;
                 label.style.position = 'absolute';
                 label.style.color = 'white';
                 label.style.backgroundColor = 'blue';
                 label.style.padding = '2px 4px';
                 label.style.borderRadius = '3px';
                 label.style.fontSize = '12px';
                 label.style.top = `${rect.top + window.scrollY - 20}px`; // Position slightly above the bounding box
                 label.style.left = `${rect.left + window.scrollX}px`;
                 label.style.zIndex = '2147483648'; // Ensure label appears above bounding box
                 highlightContainer.appendChild(label);

                Object.keys(element).forEach(key => {
                    if (element[key] === null) {
                        delete element[key];
                    }
                });

                 // Remove keys with null values
                 Object.keys(element).forEach(key => {
                    if (element[key] === null) {
                        delete element[key];
                    }
                });

                elements.push(element);
                index += 1;
            }
        });

        // Recursively process shadow roots
        node.querySelectorAll('*').forEach(el => {
            if (el.shadowRoot) {
                processNode(el.shadowRoot, index);
            }
        });
    };

    // Start processing from the document root
    processNode(document, 0);

    return elements;
}
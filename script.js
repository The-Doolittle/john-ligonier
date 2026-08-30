// script.js
let slideIndex = 0;
let autoSlideTimer = null;

function showSlides(n) {
    const slides = document.querySelectorAll('.carousel-slide');
    if (slides.length === 0) return; // Only run if there is a carousel on the page
    
    if (n >= slides.length) { slideIndex = 0; }
    if (n < 0) { slideIndex = slides.length - 1; }
    
    slides.forEach(slide => slide.classList.remove('active'));
    slides[slideIndex].classList.add('active');
}

function changeSlide(n) {
    slideIndex += n;
    showSlides(slideIndex);
    resetAutoSlide();
}

function resetAutoSlide() {
    if (autoSlideTimer) {
        clearInterval(autoSlideTimer);
    }

    autoSlideTimer = setInterval(() => {
        slideIndex += 1;
        showSlides(slideIndex);
    }, 5000);
}

function initializeNameRotation() {
    const title = document.querySelector('header h1');
    const subtitle = document.querySelector('.pseudonym');
    if (!title || !subtitle) return;

    const defaultName = 'Ralph Kinney Bennett';
    const dateText = 'March 3, 1941 – December 18, 2024';

    title.textContent = defaultName;
    subtitle.textContent = dateText;
}

document.addEventListener('DOMContentLoaded', () => {
    const mainContent = document.querySelector('main');
    
    // Gentle fade-in effect for the main content
    if (mainContent) {
        mainContent.style.transition = 'opacity 1.5s ease-in-out';
        setTimeout(() => {
            mainContent.style.opacity = '1';
        }, 100);
    }

    // Highlight the active navigation link based on current URL
    const currentLocation = location.href;
    const navLinks = document.querySelectorAll('nav a');
    
    for (let i = 0; i < navLinks.length; i++) {
        if (navLinks[i].href === currentLocation) {
            navLinks[i].className = "active";
        }
    }

    initializeNameRotation();

    const archiveSearch = document.getElementById('archive-search');
    const archiveList = document.getElementById('archive-list');
    const archiveFilters = document.getElementById('archive-filters');
    const emptyState = document.getElementById('archive-empty-state');
    let currentFilter = null;
    let allArticles = [];

    const buildFilterChips = (articles) => {
        if (!archiveFilters) return;

        const values = {
            publication: new Set(),
            year: new Set(),
            topic: new Set()
        };

        articles.forEach((article) => {
            const publication = article.publication || article.category || 'General';
            const year = article.year || 'Undated';
            const topics = article.topics || [];

            values.publication.add(publication);
            values.year.add(year);
            topics.forEach((topic) => values.topic.add(topic));
        });

        archiveFilters.innerHTML = '';

        const orderedTypes = [
            { key: 'publication', label: 'Publication' },
            { key: 'year', label: 'Year' },
            { key: 'topic', label: 'Topics' }
        ];

        orderedTypes.forEach(({ key, label }) => {
            const group = document.createElement('div');
            group.className = 'archive-filter-group';

            const caption = document.createElement('span');
            caption.className = 'archive-filter-caption';
            caption.textContent = label;
            group.appendChild(caption);

            const row = document.createElement('div');
            row.className = 'archive-filter-row';

            if (key === 'publication') {
                const allChip = document.createElement('button');
                allChip.type = 'button';
                allChip.className = 'archive-filter-chip is-active';
                allChip.dataset.filterType = 'all';
                allChip.dataset.filterValue = 'all';
                allChip.textContent = 'All';
                allChip.addEventListener('click', () => {
                    currentFilter = null;
                    updateFilterChipState();
                    filterArchiveItems();
                });
                row.appendChild(allChip);
            }

            [...values[key]].sort((a, b) => a.localeCompare(b)).forEach((value) => {
                const chip = document.createElement('button');
                chip.type = 'button';
                chip.className = 'archive-filter-chip';
                chip.textContent = value;
                chip.dataset.filterType = key;
                chip.dataset.filterValue = value;
                chip.title = `Filter by ${label}: ${value}`;
                chip.addEventListener('click', () => {
                    currentFilter = { type: key, value };
                    updateFilterChipState();
                    filterArchiveItems();
                });
                row.appendChild(chip);
            });

            group.appendChild(row);
            archiveFilters.appendChild(group);
        });

        updateFilterChipState();
    };

    const updateFilterChipState = () => {
        if (!archiveFilters) return;

        const buttons = archiveFilters.querySelectorAll('.archive-filter-chip');
        buttons.forEach((button) => {
            const isSelected = currentFilter &&
                button.dataset.filterType === currentFilter.type &&
                button.dataset.filterValue === currentFilter.value;
            const isAllSelected = !currentFilter && button.dataset.filterType === 'all';
            button.classList.toggle('is-active', isSelected || isAllSelected);
        });
    };

    const filterArchiveItems = () => {
        if (!archiveList) return;

        const term = archiveSearch ? archiveSearch.value.trim().toLowerCase() : '';
        const cards = archiveList.querySelectorAll('.archive-item');
        let visibleCount = 0;

        cards.forEach((item) => {
            const title = (item.dataset.title || '').toLowerCase();
            const searchText = (item.dataset.search || '').toLowerCase();
            const matchesTerm = !term || searchText.includes(term) || title.includes(term);
            const matchesFilter = !currentFilter || (() => {
                const value = currentFilter.value.toLowerCase();
                const articleScope = (item.dataset.filterScope || '').toLowerCase();
                return articleScope.includes(value);
            })();

            const matches = matchesTerm && matchesFilter;
            item.hidden = !matches;
            if (matches) visibleCount += 1;
        });

        if (emptyState) {
            emptyState.hidden = visibleCount !== 0;
        }
    };

    const renderArchiveItems = (articles) => {
        if (!archiveList) return;

        allArticles = articles;
        archiveList.innerHTML = '';

        articles.forEach((article) => {
            const card = document.createElement('article');
            card.className = 'archive-item';
            card.dataset.title = article.title || '';
            card.dataset.search = [
                article.title || '',
                article.publication || article.category || '',
                article.year || '',
                ...(article.topics || [])
            ].join(' ').toLowerCase();
            card.dataset.filterScope = [
                article.publication || article.category || '',
                article.year || '',
                ...(article.topics || [])
            ].join(' ');

            const title = document.createElement('h3');
            const link = document.createElement('a');
            link.href = article.link;
            link.textContent = article.title;
            title.appendChild(link);

            const description = document.createElement('p');
            description.className = 'archive-excerpt';
            description.textContent = article.excerpt || '';

            const tags = document.createElement('div');
            tags.className = 'archive-tags';

            const tagValues = [
                { value: article.publication || article.category || 'General', className: 'tag-publication' },
                { value: article.year || 'Undated', className: 'tag-year' },
                ...(article.topics || []).slice(0, 2).map((topic) => ({
                    value: topic,
                    className: 'tag-topic'
                }))
            ];

            tagValues.forEach(({ value, className }) => {
                const chip = document.createElement('span');
                chip.className = `archive-tag ${className}`;
                chip.textContent = value;
                tags.appendChild(chip);
            });

            card.appendChild(title);
            card.appendChild(description);
            card.appendChild(tags);
            archiveList.appendChild(card);
        });

        buildFilterChips(articles);
        filterArchiveItems();
    };

    if (archiveSearch) {
        archiveSearch.addEventListener('input', filterArchiveItems);
    }

    if (archiveList && archiveSearch) {
        fetch('generated/archive-data.json')
            .then((response) => response.ok ? response.json() : Promise.reject(new Error('Unable to load archive data')))
            .then((data) => {
                renderArchiveItems(data.articles || []);
            })
            .catch(() => {
                archiveList.innerHTML = '<p class="archive-empty-state">Archive data could not be loaded.</p>';
                if (emptyState) {
                    emptyState.hidden = true;
                }
            });
    }

    // Initialize carousel if it exists on the page
    showSlides(slideIndex);
    resetAutoSlide();
});
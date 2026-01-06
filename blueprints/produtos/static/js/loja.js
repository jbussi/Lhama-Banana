document.addEventListener('DOMContentLoaded', function() {
    const productGrid = document.getElementById('product-grid');
    const filtersSidebar = document.getElementById('filters-sidebar');
    const toggleFiltersBtn = document.getElementById('toggle-filters-btn');
    const clearFiltersBtn = document.getElementById('clear-filters-btn');
    const productsCountText = document.getElementById('products-count-text');
    
    // Estado dos filtros
    let activeFilters = {
        categoria_id: [],
        tamanho_id: [],
        estampa_id: [],
        preco_min: null,
        preco_max: null
    };
    
    let filtersData = null;
    
    /**
     * Carrega os filtros disponíveis do backend
     */
    async function loadFilters() {
        try {
            const response = await fetch('/api/store/filters');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            filtersData = await response.json();
            renderFilters(filtersData);
        } catch (error) {
            console.error('Erro ao carregar filtros:', error);
        }
    }
    
    /**
     * Renderiza os filtros na barra lateral
     */
    function renderFilters(filters) {
        // Renderizar categorias
        const categoryContainer = document.getElementById('category-filters');
        categoryContainer.innerHTML = '';
        filters.categorias.forEach(cat => {
            const btn = document.createElement('button');
            btn.className = 'filter-btn';
            btn.dataset.filterType = 'categoria';
            btn.dataset.filterId = cat.id;
            btn.textContent = cat.nome;
            btn.addEventListener('click', () => toggleFilter('categoria_id', cat.id, btn));
            categoryContainer.appendChild(btn);
        });
        
        // Renderizar tamanhos
        const sizeContainer = document.getElementById('size-filters');
        sizeContainer.innerHTML = '';
        filters.tamanhos.forEach(tam => {
            const btn = document.createElement('button');
            btn.className = 'filter-btn';
            btn.dataset.filterType = 'tamanho';
            btn.dataset.filterId = tam.id;
            btn.textContent = tam.nome;
            btn.addEventListener('click', () => toggleFilter('tamanho_id', tam.id, btn));
            sizeContainer.appendChild(btn);
        });
        
        // Renderizar estampas
        const estampaContainer = document.getElementById('estampa-filters');
        estampaContainer.innerHTML = '';
        filters.estampas.forEach(est => {
            const btn = document.createElement('button');
            btn.className = 'filter-btn estampa-btn';
            btn.dataset.filterType = 'estampa';
            btn.dataset.filterId = est.id;
            
            const img = document.createElement('img');
            img.src = est.imagem_url || '/static/img/placeholder.jpg';
            img.alt = est.nome;
            
            const span = document.createElement('span');
            span.textContent = est.nome;
            
            btn.appendChild(img);
            btn.appendChild(span);
            btn.addEventListener('click', () => toggleFilter('estampa_id', est.id, btn));
            estampaContainer.appendChild(btn);
        });
        
        // Renderizar faixas de preço
        const priceContainer = document.getElementById('price-filters');
        priceContainer.innerHTML = '';
        filters.precos.forEach(preco => {
            const btn = document.createElement('button');
            btn.className = 'filter-btn';
            btn.dataset.filterType = 'preco';
            btn.dataset.precoMin = preco.min;
            btn.dataset.precoMax = preco.max || '';
            btn.textContent = preco.label;
            btn.addEventListener('click', () => togglePriceFilter(preco.min, preco.max, btn));
            priceContainer.appendChild(btn);
        });
    }
    
    /**
     * Alterna um filtro (categoria, tamanho, estampa)
     */
    function toggleFilter(filterKey, filterId, button) {
        const index = activeFilters[filterKey].indexOf(filterId);
        
        if (index > -1) {
            // Remove o filtro
            activeFilters[filterKey].splice(index, 1);
            button.classList.remove('active');
        } else {
            // Adiciona o filtro
            activeFilters[filterKey].push(filterId);
            button.classList.add('active');
        }
        
        // Aplicar filtros
        applyFilters();
    }
    
    /**
     * Alterna filtro de preço (apenas um pode estar ativo)
     */
    function togglePriceFilter(min, max, button) {
        // Remove active de todos os botões de preço
        document.querySelectorAll('#price-filters .filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        if (activeFilters.preco_min === min && activeFilters.preco_max === max) {
            // Se já estava ativo, desativa
            activeFilters.preco_min = null;
            activeFilters.preco_max = null;
        } else {
            // Ativa o novo filtro
            activeFilters.preco_min = min;
            activeFilters.preco_max = max;
            button.classList.add('active');
        }
        
        applyFilters();
    }
    
    /**
     * Limpa todos os filtros
     */
    function clearAllFilters() {
        activeFilters = {
            categoria_id: [],
            tamanho_id: [],
            estampa_id: [],
            preco_min: null,
            preco_max: null
        };
        
        // Remove active de todos os botões
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        applyFilters();
    }
    
    /**
     * Aplica os filtros e busca produtos
     */
    async function applyFilters() {
        // Construir query string
        const params = new URLSearchParams();
        
        activeFilters.categoria_id.forEach(id => {
            params.append('categoria_id', id);
        });
        
        activeFilters.tamanho_id.forEach(id => {
            params.append('tamanho_id', id);
        });
        
        activeFilters.estampa_id.forEach(id => {
            params.append('estampa_id', id);
        });
        
        if (activeFilters.preco_min !== null) {
            params.append('preco_min', activeFilters.preco_min);
        }
        
        if (activeFilters.preco_max !== null) {
            params.append('preco_max', activeFilters.preco_max);
        }
        
        // Buscar produtos com filtros
        await fetchAndRenderProducts(params.toString());
    }
    
    /**
     * Busca e renderiza produtos do backend
     */
    async function fetchAndRenderProducts(queryString = '') {
        try {
            productGrid.innerHTML = '<div class="loading-message">Carregando produtos...</div>';
            
            const url = queryString ? `/api/base_products?${queryString}` : '/api/base_products';
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const products = await response.json();
            console.log("Produtos recebidos:", products);
            
            renderProducts(products);
            updateProductsCount(products.length);
            
        } catch (error) {
            console.error('Erro ao buscar produtos:', error);
            productGrid.innerHTML = '<div class="loading-message">Não foi possível carregar os produtos. Tente novamente mais tarde.</div>';
        }
    }
    
    /**
     * Renderiza os produtos no grid
     */
    function renderProducts(products) {
        productGrid.innerHTML = '';
        
        if (products.length === 0) {
            productGrid.innerHTML = '<div class="loading-message">Nenhum produto encontrado com os filtros selecionados.</div>';
            return;
        }
        
        products.forEach(product => {
            const priceDisplay = product.preco_minimo !== null ?
                `R$ ${product.preco_minimo.toFixed(2).replace('.', ',')}` :
                'Preço indisponível';
            
            let statusBadgeText = '';
            let statusBadgeClass = '';
            if (product.estoque > 0) {
                statusBadgeText = 'Em Estoque';
                statusBadgeClass = 'status-in-stock';
            } else {
                statusBadgeText = 'Sob Demanda';
                statusBadgeClass = 'status-out-of-stock';
            }
            
            const productCard = `
                <div class="product-card">
                    <a href="/produtos/${product.id}" style="text-decoration: none; color: inherit;">
                        <div class="product-image">
                            <img src="${product.imagem_url}" alt="${product.nome}">
                            <span class="product-badge ${statusBadgeClass}">${statusBadgeText}</span>
                        </div>
                        <div class="product-info">
                            <span class="product-category">${product.categoria}</span>
                            <h3>${product.nome}</h3>
                            <p class="product-description">${product.descricao || ''}</p>
                        </div>
                    </a>
                    <div class="product-footer">
                        <div class="price">${priceDisplay}</div>
                        <button class="add-to-cart-btn" onclick="window.location.href='/produtos/${product.id}'">
                            <i class="fas fa-eye"></i> Ver Detalhes
                        </button>
                    </div>
                </div>
            `;
            
            productGrid.innerHTML += productCard;
        });
    }
    
    /**
     * Atualiza o contador de produtos
     */
    function updateProductsCount(count) {
        const text = count === 1 ? '1 produto encontrado' : `${count} produtos encontrados`;
        productsCountText.textContent = text;
    }
    
    /**
     * Toggle da barra lateral em mobile
     */
    if (toggleFiltersBtn) {
        toggleFiltersBtn.addEventListener('click', () => {
            filtersSidebar.classList.toggle('open');
        });
    }
    
    /**
     * Limpar filtros
     */
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearAllFilters);
    }
    
    // Fechar sidebar ao clicar fora (mobile)
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 992) {
            if (!filtersSidebar.contains(e.target) && 
                !toggleFiltersBtn.contains(e.target) && 
                filtersSidebar.classList.contains('open')) {
                filtersSidebar.classList.remove('open');
            }
        }
    });
    
    // Inicialização
    loadFilters();
    fetchAndRenderProducts();
});

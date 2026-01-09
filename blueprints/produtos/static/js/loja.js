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
        tecido: [],
        sexo: [],
        preco_min: null,
        preco_max: null
    };
    
    let filtersData = null;
    
    /**
     * Carrega os filtros disponíveis do backend
     */
    async function loadFilters() {
        try {
            console.log('Carregando filtros...');
            const response = await fetch('/api/store/filters');
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error(`Erro HTTP ${response.status}:`, errorText);
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            filtersData = await response.json();
            console.log('Filtros recebidos:', filtersData);
            
            if (!filtersData) {
                throw new Error('Resposta vazia do servidor');
            }
            
            renderFilters(filtersData);
        } catch (error) {
            console.error('Erro ao carregar filtros:', error);
            
            // Mostrar mensagem de erro nos containers
            const containers = [
                'category-filters',
                'size-filters',
                'estampa-filters',
                'tecido-filters',
                'sexo-filters',
                'price-filters'
            ];
            
            containers.forEach(containerId => {
                const container = document.getElementById(containerId);
                if (container) {
                    container.innerHTML = `<div class="filter-loading" style="color: #dc3545;">Erro ao carregar filtros. Recarregue a página.</div>`;
                }
            });
        }
    }
    
    /**
     * Renderiza os filtros na barra lateral
     */
    function renderFilters(filters) {
        if (!filters) {
            console.error('Filtros não fornecidos');
            return;
        }
        
        console.log('Renderizando filtros:', filters);
        
        // Renderizar categorias
        const categoryContainer = document.getElementById('category-filters');
        if (!categoryContainer) {
            console.error('Container category-filters não encontrado');
            return;
        }
        categoryContainer.innerHTML = '';
        
        if (!filters.categorias || !Array.isArray(filters.categorias) || filters.categorias.length === 0) {
            categoryContainer.innerHTML = '<div class="filter-loading">Nenhuma categoria disponível</div>';
        } else {
            filters.categorias.forEach(cat => {
                if (!cat || !cat.id || !cat.nome) {
                    console.warn('Categoria inválida:', cat);
                    return;
                }
                const btn = document.createElement('button');
                btn.className = 'filter-btn';
                btn.dataset.filterType = 'categoria';
                btn.dataset.filterId = cat.id;
                btn.textContent = cat.nome;
                btn.addEventListener('click', () => toggleFilter('categoria_id', cat.id, btn));
                categoryContainer.appendChild(btn);
            });
        }
        
        // Renderizar tamanhos
        const sizeContainer = document.getElementById('size-filters');
        if (!sizeContainer) {
            console.error('Container size-filters não encontrado');
            return;
        }
        sizeContainer.innerHTML = '';
        
        if (!filters.tamanhos || !Array.isArray(filters.tamanhos) || filters.tamanhos.length === 0) {
            sizeContainer.innerHTML = '<div class="filter-loading">Nenhum tamanho disponível</div>';
        } else {
            filters.tamanhos.forEach(tam => {
                if (!tam || !tam.id || !tam.nome) {
                    console.warn('Tamanho inválido:', tam);
                    return;
                }
                const btn = document.createElement('button');
                btn.className = 'filter-btn';
                btn.dataset.filterType = 'tamanho';
                btn.dataset.filterId = tam.id;
                btn.textContent = tam.nome;
                btn.addEventListener('click', () => toggleFilter('tamanho_id', tam.id, btn));
                sizeContainer.appendChild(btn);
            });
        }
        
        // Renderizar estampas
        const estampaContainer = document.getElementById('estampa-filters');
        if (!estampaContainer) {
            console.error('Container estampa-filters não encontrado');
            return;
        }
        estampaContainer.innerHTML = '';
        
        if (!filters.estampas || !Array.isArray(filters.estampas) || filters.estampas.length === 0) {
            estampaContainer.innerHTML = '<div class="filter-loading">Nenhuma estampa disponível</div>';
        } else {
            filters.estampas.forEach(est => {
                if (!est || !est.id || !est.nome) {
                    console.warn('Estampa inválida:', est);
                    return;
                }
                const btn = document.createElement('button');
                btn.className = 'filter-btn estampa-btn';
                btn.dataset.filterType = 'estampa';
                btn.dataset.filterId = est.id;
                
                const img = document.createElement('img');
                img.src = est.imagem_url || '/static/img/placeholder.jpg';
                img.alt = est.nome || 'Estampa';
                
                const span = document.createElement('span');
                span.textContent = est.nome || 'Sem nome';
                
                btn.appendChild(img);
                btn.appendChild(span);
                btn.addEventListener('click', () => toggleFilter('estampa_id', est.id, btn));
                estampaContainer.appendChild(btn);
            });
        }
        
        // Renderizar tecidos
        const tecidoContainer = document.getElementById('tecido-filters');
        if (!tecidoContainer) {
            console.error('Container tecido-filters não encontrado');
            return;
        }
        tecidoContainer.innerHTML = '';
        
        if (!filters.tecidos || !Array.isArray(filters.tecidos) || filters.tecidos.length === 0) {
            tecidoContainer.innerHTML = '<div class="filter-loading">Nenhum tecido disponível</div>';
        } else {
            filters.tecidos.forEach(tec => {
                if (!tec || !tec.value || !tec.label) {
                    console.warn('Tecido inválido:', tec);
                    return;
                }
                const btn = document.createElement('button');
                btn.className = 'filter-btn';
                btn.dataset.filterType = 'tecido';
                btn.dataset.filterValue = tec.value;
                btn.textContent = tec.label;
                btn.addEventListener('click', () => toggleFilter('tecido', tec.value, btn));
                tecidoContainer.appendChild(btn);
            });
        }
        
        // Renderizar sexos
        const sexoContainer = document.getElementById('sexo-filters');
        if (!sexoContainer) {
            console.error('Container sexo-filters não encontrado');
            return;
        }
        sexoContainer.innerHTML = '';
        
        if (!filters.sexos || !Array.isArray(filters.sexos) || filters.sexos.length === 0) {
            sexoContainer.innerHTML = '<div class="filter-loading">Nenhuma opção disponível</div>';
        } else {
            filters.sexos.forEach(sex => {
                if (!sex || !sex.value || !sex.label) {
                    console.warn('Sexo inválido:', sex);
                    return;
                }
                const btn = document.createElement('button');
                btn.className = 'filter-btn';
                btn.dataset.filterType = 'sexo';
                btn.dataset.filterValue = sex.value;
                btn.textContent = sex.label;
                btn.addEventListener('click', () => toggleFilter('sexo', sex.value, btn));
                sexoContainer.appendChild(btn);
            });
        }
        
        // Renderizar faixas de preço
        const priceContainer = document.getElementById('price-filters');
        if (!priceContainer) {
            console.error('Container price-filters não encontrado');
            return;
        }
        priceContainer.innerHTML = '';
        
        if (!filters.precos || !Array.isArray(filters.precos) || filters.precos.length === 0) {
            priceContainer.innerHTML = '<div class="filter-loading">Nenhuma faixa de preço disponível</div>';
        } else {
            filters.precos.forEach(preco => {
                if (!preco || preco.min === undefined || !preco.label) {
                    console.warn('Preço inválido:', preco);
                    return;
                }
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
        
        console.log('Filtros renderizados com sucesso');
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
            tecido: [],
            sexo: [],
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
        
        activeFilters.tecido.forEach(tec => {
            params.append('tecido', tec);
        });
        
        activeFilters.sexo.forEach(sex => {
            params.append('sexo', sex);
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
            // Formatar preço com promoção se existir
            let priceDisplay = '';
            if (product.preco_minimo !== null) {
                if (product.tem_promocao && product.preco_minimo_original !== null && product.preco_minimo < product.preco_minimo_original) {
                    // Com promoção: mostrar preço promocional e preço original riscado
                    const descontoPercentual = Math.round(((product.preco_minimo_original - product.preco_minimo) / product.preco_minimo_original) * 100);
                    priceDisplay = `
                        <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
                            <span class="price-promo">R$ ${product.preco_minimo.toFixed(2).replace('.', ',')}</span>
                            <span class="old-price">R$ ${product.preco_minimo_original.toFixed(2).replace('.', ',')}</span>
                            <span class="discount-badge-card">${descontoPercentual}% OFF</span>
                        </div>
                    `;
                } else {
                    // Sem promoção: apenas preço normal
                    priceDisplay = `<span style="color: #2ab7a9;">R$ ${product.preco_minimo.toFixed(2).replace('.', ',')}</span>`;
                }
            } else {
                priceDisplay = '<span style="color: #6c757d;">Preço indisponível</span>';
            }

            let statusBadgeText = '';
            let statusBadgeClass = '';
            if (product.estoque > 0) {
                statusBadgeText = product.tem_promocao ? 'Promoção' : 'Em Estoque';
                statusBadgeClass = product.tem_promocao ? 'status-promocao' : 'status-in-stock';
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

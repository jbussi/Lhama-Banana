// static/js/produto_detalhes.js

// Funções para controlar a tela de carregamento
function showLoadingScreen() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.classList.remove('hidden');
    } else {
        console.error("Erro: Elemento #loading-overlay não encontrado.");
    }
}

function hideLoadingScreen() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.classList.add('hidden');
    }
}

async function getAuthHeaders() {
    const headers = {
        'Content-Type': 'application/json'
    };

    let sessionId = localStorage.getItem('cartSessionId');
    if (!sessionId) {
        sessionId = crypto.randomUUID(); // Gerar um novo UUID se não existir
        localStorage.setItem('cartSessionId', sessionId);
    }
    headers['X-Session-ID'] = sessionId;
    
    return headers;
}
// ===========

document.addEventListener('DOMContentLoaded', async function() {
    const urlSegments = window.location.pathname.split('/');
    const nomeProdutoId = urlSegments[urlSegments.length - 1];

    let productData = null;
    let selectedEstampa = null;
    let selectedTamanho = null;
    let selectedVariation = null;

    // Referências aos elementos HTML da página
    const productNameElem = document.getElementById('product-name');
    const productDescElem = document.getElementById('product-description');
    const productCategoryElem = document.getElementById('product-category');
    const productPriceElem = document.getElementById('product-price');
    const productImageGallery = document.getElementById('product-image-gallery');
    const estampaOptionsContainer = document.getElementById('estampa-options-container');
    const tamanhoOptionsContainer = document.getElementById('tamanho-options-container');
    const quantityInput = document.getElementById('quantity-input');
    const quantityMinusBtn = document.getElementById('quantity-minus-btn');
    const quantityPlusBtn = document.getElementById('quantity-plus-btn');
    const addToCartBtn = document.getElementById('add-to-cart-btn');
    const stockStatusElem = document.getElementById('stock-status');
    const skuElem = document.getElementById('product-sku');
    const productCategoryBreadcrumb = document.getElementById('product-category-breadcrumb');
    const productNameBreadcrumb = document.getElementById('product-name-breadcrumb');
    const productCategoryInfo = document.getElementById('product-category-info');
    const productTagsElem = document.getElementById('product-tags');
    const oldPriceElem = document.getElementById('old-price');
    const discountBadgeElem = document.getElementById('discount-badge');
    const descriptionTabContent = document.getElementById('description-tab-content');
    
    // Referências aos botões das abas e seus conteúdos
    const tabDescriptionBtn = document.getElementById('tab-description-btn');
    const tabDetailsBtn = document.getElementById('tab-details-btn');
    const tabReviewsBtn = document.getElementById('tab-reviews-btn');
    const descriptionTab = document.getElementById('descriptionTab');
    const detailsTab = document.getElementById('detailsTab');
    const reviewsTab = document.getElementById('reviewsTab');
    const reviewsList = document.getElementById('reviews-list');
    const reviewsCountElem = document.getElementById('reviews-count');
    const writeReviewBtn = document.getElementById('write-review-btn');
    const buyNowBtn = document.getElementById('buy-now-btn');


    /**
     * Função assíncrona para buscar os detalhes do produto do backend.
     */
    async function fetchProductDetails() {

        try {
            const response = await fetch(`/api/base_products/${nomeProdutoId}`);

            if (!response.ok) {
                if (response.status === 404) {
                    const errorContainer = document.getElementById('main-product-container') || document.body;
                    errorContainer.innerHTML = `
                        <div style="text-align: center; padding: 50px;">
                            <h2>Ops! Produto não encontrado :(</h2>
                            <p>Parece que o produto que você está procurando não existe ou foi removido.</p>
                            <p><a href="/loja" style="text-decoration: underline; color: #007bff;">Voltar para a Loja</a></p>
                        </div>
                    `;
                    throw new Error(`Product not found: status ${response.status}`);
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            productData = await response.json();
            console.log("Detalhes do produto recebidos:", productData);

            // Preenche as informações básicas do produto na página
            productNameElem.textContent = productData.nome;
            productDescElem.textContent = productData.descricao;
            productCategoryElem.textContent = productData.categoria;

            productCategoryBreadcrumb.textContent = productData.categoria;
            productNameBreadcrumb.textContent = productData.nome;
            productCategoryInfo.textContent = productData.categoria;
            descriptionTabContent.innerHTML = productData.descricao; // Para a aba de descrição

            // Popula os seletores de estampa e tamanho com base nas variações disponíveis
            populateVariationSelectors(productData.variations);

            // Preencher detalhes adicionais (abas) - MOCADO por enquanto, para combinar com o HTML original
            // Você precisaria de mais dados no backend para preencher isso dinamicamente
            // e alterar a API get_product_details para retornar esses campos
            document.getElementById('detail-material').textContent = 'Algodão 100%';
            document.getElementById('detail-cor').textContent = 'Varia conforme o modelo';
            document.getElementById('detail-tamanho').textContent = 'P, M, G, GG';
            document.getElementById('detail-peso').textContent = '200g';
            document.getElementById('detail-composicao').textContent = '95% Algodão, 5% Elastano';
            document.getElementById('detail-instrucoes').textContent = 'Lavar na máquina com água fria, não usar alvejante, secar à sombra';

            // Preencher avaliações (mocadas por enquanto)
            const reviews = [
                {'user': 'Cliente Satisfeito', 'rating': 5, 'comment': 'Adorei o produto!', 'date': '10/07/2024'},
                {'user': 'Comprador Feliz', 'rating': 4, 'comment': 'Muito bom, recomendo!', 'date': '09/07/2024'}
            ];
            renderReviews(reviews);
            reviewsCountElem.textContent = reviews.length;

            // Preencher Tags (mocadas por enquanto)
            const tags = ['lhamas', 'infantil', 'conforto'];
            if (productTagsElem) {
                 productTagsElem.innerHTML = tags.map(tag => `<a href="#" class="tag">${tag}</a>`).join(', ');
            }


        } catch (error) {
            console.error('Erro ao buscar detalhes do produto:', error);
            if (!productData) {
                const errorContainer = document.getElementById('main-product-container') || document.body;
                errorContainer.innerHTML = '<div style="text-align: center; padding: 50px;"><p>Ocorreu um erro ao carregar os detalhes do produto. Tente novamente mais tarde.</p></div>';
            }
        } finally {
        }
    }

    /**
     * Popula os seletores de estampa e tamanho com opções únicas.
     */
    function populateVariationSelectors(variations) {
        // Obter estampas e tamanhos únicos
        const uniqueEstampas = Array.from(new Set(variations.map(v => v.estampa.nome)))
                                    .sort((a, b) => a.localeCompare(b));
        const uniqueTamanhos = Array.from(new Set(variations.map(v => v.tamanho.nome)))
                                     .sort((a, b) => {
                                         const order = {'P': 1, 'M': 2, 'G': 3, 'GG': 4, 'XG': 5};
                                         return (order[a] || 99) - (order[b] || 99);
                                     });

        if (estampaOptionsContainer) estampaOptionsContainer.innerHTML = '';
        if (tamanhoOptionsContainer) tamanhoOptionsContainer.innerHTML = '';

        // Popula as opções de estampa como divs
        uniqueEstampas.forEach(estampaName => {
            const estampaDiv = document.createElement('div');
            estampaDiv.classList.add('color-option');
            estampaDiv.style.backgroundColor = getEstampaColor(estampaName); // Use cores fictícias ou do DB
            estampaDiv.title = estampaName;
            estampaDiv.dataset.estampaNome = estampaName;
            estampaDiv.addEventListener('click', () => {
                selectOption(estampaOptionsContainer, estampaDiv, 'estampa', estampaName);
            });
            if (estampaOptionsContainer) estampaOptionsContainer.appendChild(estampaDiv);
        });

        // Popula as opções de tamanho como divs
        uniqueTamanhos.forEach(tamanhoName => {
            const tamanhoDiv = document.createElement('div');
            tamanhoDiv.classList.add('size-option');
            tamanhoDiv.textContent = tamanhoName;
            tamanhoDiv.dataset.tamanhoNome = tamanhoName;
            tamanhoDiv.addEventListener('click', () => {
                selectOption(tamanhoOptionsContainer, tamanhoDiv, 'tamanho', tamanhoName);
            });
            if (tamanhoOptionsContainer) tamanhoOptionsContainer.appendChild(tamanhoDiv);
        });

        // Seleciona a primeira estampa e o primeiro tamanho como padrão
        if (uniqueEstampas.length > 0 && estampaOptionsContainer.firstElementChild) {
            selectOption(estampaOptionsContainer, estampaOptionsContainer.firstElementChild, 'estampa', uniqueEstampas[0]);
        }
        if (uniqueTamanhos.length > 0 && tamanhoOptionsContainer.firstElementChild) {
            selectOption(tamanhoOptionsContainer, tamanhoOptionsContainer.firstElementChild, 'tamanho', uniqueTamanhos[0]);
        }
    }

    /**
     * Helper para obter uma cor fictícia baseada no nome da estampa.
     * SUBSTITUA ISSO PELA URL REAL DA IMAGEM DA ESTAMPA OU CÓDIGO DE COR SE DISPONÍVEL NO DB.
     */
    function getEstampaColor(estampaName) {
        const colors = {
            'Lhama Feliz': '#90EE90',
            'Banana Estilosa': '#FFD700',
            'Floral Encantado': '#FFB6C1',
            'Astronauta Aventureiro': '#A9A9A9',
            'Dinossauro Radical': '#8B4513'
        };
        return colors[estampaName] || '#CCCCCC';
    }


    /**
     * Função para gerenciar a seleção de opções (estampa/tamanho).
     */
    function selectOption(container, selectedElement, type, value) {
        if (!container) return; // Garante que o contêiner exista

        Array.from(container.children).forEach(el => el.classList.remove('selected'));
        selectedElement.classList.add('selected');

        if (type === 'estampa') {
            selectedEstampa = value;
        } else if (type === 'tamanho') {
            selectedTamanho = value;
        }
        updateProductSelection();
    }

    /**
     * Atualiza a variação selecionada quando o usuário muda as opções.
     */
    function updateProductSelection() {
        if (!selectedEstampa || !selectedTamanho || !productData) {
            return;
        }

        const foundVariation = productData.variations.find(v =>
            v.estampa.nome === selectedEstampa && v.tamanho.nome === selectedTamanho
        );

        if (foundVariation) {
            updateSelectedVariation(foundVariation);
        } else {
            productPriceElem.textContent = 'R$ N/A';
            oldPriceElem.style.display = 'none';
            discountBadgeElem.style.display = 'none';
            stockStatusElem.textContent = 'Combinação indisponível.';
            skuElem.textContent = 'SKU: -';
            if (addToCartBtn) addToCartBtn.disabled = true;
            if (buyNowBtn) buyNowBtn.disabled = true;
            quantityInput.value = 0;
            quantityInput.max = 0;
            if (productImageGallery) productImageGallery.innerHTML = '<p>Esta combinação não está disponível.</p>';
        }
    }

    /**
     * Atualiza a interface do usuário com os detalhes da variação selecionada.
     */
    function updateSelectedVariation(variation) {
        selectedVariation = variation;

        productPriceElem.textContent = `R$ ${variation.preco.toFixed(2).replace('.', ',')}`;
        oldPriceElem.style.display = 'none';
        discountBadgeElem.style.display = 'none';
        // Você pode implementar a lógica de preço antigo/desconto aqui se tiver esses dados no backend

        skuElem.textContent = `SKU: ${variation.sku}`;
        quantityInput.value = 1;

        if (variation.estoque > 0) {
            stockStatusElem.textContent = `Em estoque: ${variation.estoque} unidades.`;
            if (addToCartBtn) {
                addToCartBtn.textContent = 'Adicionar ao Carrinho';
                addToCartBtn.disabled = false;
            }
            if (buyNowBtn) buyNowBtn.disabled = false;
            quantityInput.max = variation.estoque;
        } else {
            stockStatusElem.textContent = 'Esgotado.';
            if (addToCartBtn) {
                addToCartBtn.textContent = 'Indisponível';
                addToCartBtn.disabled = true;
            }
            if (buyNowBtn) buyNowBtn.disabled = true;
            quantityInput.max = 0;
        }

        // Atualiza a galeria de imagens
        if (productImageGallery) productImageGallery.innerHTML = '';
        const mainImageContainer = document.createElement('div');
        mainImageContainer.classList.add('product-main-image-container');
        const thumbnailsContainer = document.createElement('div');
        thumbnailsContainer.classList.add('product-thumbnails');

        if (variation.images && variation.images.length > 0) {
            const mainImg = document.createElement('img');
            mainImg.src = variation.images[0].url;
            mainImg.alt = variation.images[0].descricao || `${productData.nome} - ${variation.estampa.nome} - ${variation.tamanho.nome}`;
            mainImg.classList.add('product-main-image');
            mainImg.id = 'mainImage';
            mainImageContainer.appendChild(mainImg);
            
            variation.images.forEach((img, index) => {
                const thumbImg = document.createElement('img');
                thumbImg.src = img.url;
                thumbImg.alt = img.descricao || `Miniatura ${index + 1}`;
                thumbImg.classList.add('thumbnail');
                if (index === 0) {
                    thumbImg.classList.add('active');
                }
                thumbImg.addEventListener('click', () => {
                    document.getElementById('mainImage').src = thumbImg.src;
                    Array.from(thumbnailsContainer.children).forEach(t => t.classList.remove('active'));
                    thumbImg.classList.add('active');
                });
                thumbnailsContainer.appendChild(thumbImg);
            });
            if (productImageGallery) {
                productImageGallery.appendChild(mainImageContainer);
                productImageGallery.appendChild(thumbnailsContainer);
            }

        } else {
            if (productImageGallery) {
                productImageGallery.innerHTML = '<p>Nenhuma imagem disponível para esta variação.</p>';
                const placeholderImg = document.createElement('img');
                placeholderImg.src = '/static/img/placeholder.jpg';
                placeholderImg.alt = 'Imagem Indisponível';
                placeholderImg.classList.add('product-main-image');
                mainImageContainer.appendChild(placeholderImg);
                productImageGallery.appendChild(mainImageContainer);
            }
        }
    }

    // --- Lógica de Quantidade ---
    if (quantityMinusBtn) {
        quantityMinusBtn.addEventListener('click', () => {
            let currentValue = parseInt(quantityInput.value);
            if (currentValue > quantityInput.min) {
                quantityInput.value = currentValue - 1;
            }
        });
    }

    if (quantityPlusBtn) {
        quantityPlusBtn.addEventListener('click', () => {
            let currentValue = parseInt(quantityInput.value);
            if (currentValue < quantityInput.max) {
                quantityInput.value = currentValue + 1;
            }
        });
    }

    // --- Lógica do Carrinho (Placeholder) ---
    if (addToCartBtn) {
        addToCartBtn.addEventListener('click', async () => { // Adicionado 'async' aqui
            if (!selectedVariation) {
                alert('Por favor, selecione uma variação do produto.');
                return;
            }
            const quantity = parseInt(quantityInput.value);
            if (isNaN(quantity) || quantity <= 0) {
                alert('Por favor, insira uma quantidade válida.');
                return;
            }
            if (quantity > selectedVariation.estoque) {
                alert(`A quantidade desejada excede o estoque disponível (${selectedVariation.estoque}).`);
                return;
            }
            
            try {
                const response = await fetch('/api/cart/add', {
                    method: 'POST',
                    headers: await getAuthHeaders(), // Usar o helper de headers
                    body: JSON.stringify({
                        product_id: selectedVariation.id, // ID da variação do produto
                        quantity: quantity
                    })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    alert(`Erro ao adicionar ao carrinho: ${errorData.erro || 'Ocorreu um erro desconhecido.'}`);
                    console.error('Erro detalhado:', errorData);
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const responseData = await response.json();
                alert(`Sucesso! ${responseData.mensagem || 'Item adicionado ao carrinho.'}`);
                console.log('Item adicionado ao carrinho:', responseData);

                // Opcional: Atualizar algum contador de carrinho no header, etc.
                // Ou redirecionar para o carrinho: window.location.href = '/carrinho';

            } catch (error) {
                console.error('Falha ao adicionar item ao carrinho:', error);
                alert('Não foi possível adicionar o item ao carrinho. Tente novamente.');
            } finally {
            }
        });
    }

    // --- Lógica do Comprar Agora (Placeholder) ---
    if (buyNowBtn) {
        buyNowBtn.addEventListener('click', () => {
            alert('Redirecionando para o checkout com este produto...');
        });
    }
    
    // --- Lógica das Abas ---
    const tabButtons = [tabDescriptionBtn, tabDetailsBtn, tabReviewsBtn];
    const tabContents = {
        'description': descriptionTab,
        'details': detailsTab,
        'reviews': reviewsTab
    };

    tabButtons.forEach(button => {
        if (button) { // Garante que o botão existe
            button.addEventListener('click', function() {
                tabButtons.forEach(btn => { if (btn) btn.classList.remove('active'); });
                Object.values(tabContents).forEach(content => { if (content) content.style.display = 'none'; });

                this.classList.add('active');
                const targetTab = this.getAttribute('data-tab');
                if (tabContents[targetTab]) tabContents[targetTab].style.display = 'block';
            });
        }
    });

    function renderReviews(reviews) {
        if (reviewsList) reviewsList.innerHTML = '';
        if (reviews && reviews.length > 0) {
            reviews.forEach(review => {
                const reviewDiv = document.createElement('div');
                reviewDiv.classList.add('review');
                reviewDiv.innerHTML = `
                    <div class="review-header">
                        <span class="review-author">${review.user}</span>
                        <div class="review-rating">
                            ${'<i class="fas fa-star"></i>'.repeat(review.rating)}
                            ${'<i class="far fa-star"></i>'.repeat(5 - review.rating)}
                        </div>
                        <span class="review-date">${review.date}</span>
                    </div>
                    <p class="review-text">${review.comment}</p>
                `;
                if (reviewsList) reviewsList.appendChild(reviewDiv);
            });
        } else {
            if (reviewsList) reviewsList.innerHTML = '<p>Nenhuma avaliação ainda. Seja o primeiro a avaliar!</p>';
        }
    }

    // --- Lógica do Escrever Avaliação (Placeholder) ---
    if (writeReviewBtn) {
        writeReviewBtn.addEventListener('click', () => {
            alert('Formulário de avaliação será exibido aqui!');
        });
    }

    // Inicia o processo de busca e renderização dos detalhes do produto
    fetchProductDetails();
});
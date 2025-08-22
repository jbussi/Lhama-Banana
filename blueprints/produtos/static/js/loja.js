document.addEventListener('DOMContentLoaded', function() {
    // Referência para o contêiner onde os cards de produtos serão inseridos
    const productGrid = document.getElementById('product-grid');

    /**
     * Função assíncrona para buscar os produtos do backend e renderizá-los.
     */
    async function fetchAndRenderBaseProducts() {
        try {
            // Faz a requisição HTTP GET para o endpoint da sua API Flask
            // Certifique-se de que a URL corresponde ao seu servidor Flask (normalmente localhost:80)
            const response = await fetch('http://localhost:80/api/base_products');

            // Verifica se a resposta HTTP foi bem-sucedida (status 2xx)
            if (!response.ok) {
                // Se não for bem-sucedida, lança um erro com o status HTTP
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Converte o corpo da resposta para JSON
            const baseProducts = await response.json();
            
            // Exibe os dados recebidos no console para depuração
            console.log("Produtos base recebidos:", baseProducts);

            // Chama a função para renderizar os produtos na interface do usuário
            renderBaseProducts(baseProducts);

        } catch (error) {
            // Captura e exibe qualquer erro que ocorra durante a requisição ou processamento
            console.error('Erro ao buscar produtos:', error);
            // Exibe uma mensagem de erro amigável na página para o usuário
            productGrid.innerHTML = '<p>Não foi possível carregar os produtos. Tente novamente mais tarde.</p>';
        }
    }

    /**
     * Função para renderizar os cards de produtos no grid da página.
     * @param {Array} products - Um array de objetos de produto, recebidos do backend.
     */
    function renderBaseProducts(products) {
        // Limpa qualquer conteúdo existente no grid antes de adicionar novos produtos
        // Isso é importante para evitar duplicações se a função for chamada múltiplas vezes
        productGrid.innerHTML = '';

        // Verifica se há produtos para exibir
        if (products.length === 0) {
            productGrid.innerHTML = '<p>Nenhum produto encontrado.</p>';
            return;
        }

        // Itera sobre cada objeto de produto no array 'products'
        products.forEach(product => {
            // Formata o preço para exibição no formato monetário brasileiro (R$ XX,YY)
            // Se 'preco_minimo' for null ou undefined, exibe 'Preço indisponível'
            let priceDisplay = product.preco_minimo !== null ?
                               `R$ ${product.preco_minimo.toFixed(2).replace('.', ',')}` :
                               'Preço indisponível';

            // Lógica para determinar o texto do badge de status e a classe CSS
            // Baseado no valor numérico de 'estoque' (que é 'variacoes_em_estoque_count' do backend)
            let statusBadgeText = '';
            let statusBadgeClass = '';
            if (product.estoque > 0) { // Se a contagem de variações em estoque for maior que 0
                statusBadgeText = 'Em Estoque';
                statusBadgeClass = 'status-in-stock'; // Classe CSS para estilo de "em estoque"
            } else { // Se a contagem for 0 (nenhuma variação em estoque)
                statusBadgeText = 'Sob Demanda';
                statusBadgeClass = 'status-out-of-stock'; // Classe CSS para estilo de "esgotado"
            }

            // Constrói o HTML para um único card de produto usando template literals
            const productCard = `
                <div class="product-card">
                    <!-- Link para a página de detalhes do produto, passando o ID do produto base -->
                    <a href="/produtos/${product.id}" style="text-decoration: none; color: inherit;">
                        <div class="product-image">
                            <!-- A imagem do produto. O atributo 'alt' melhora a acessibilidade e SEO. -->
                            <img src="${product.imagem_url}" alt="${product.nome}">
                            <!-- O badge de status (Em Estoque/Esgotado) -->
                            <span class="product-badge ${statusBadgeClass}">${statusBadgeText}</span>
                        </div>
                        <div class="product-info">
                            <!-- Categoria do produto -->
                            <span class="product-category">${product.categoria}</span>
                            <!-- Nome do produto -->
                            <h3>${product.nome}</h3>
                            <!-- Descrição curta do produto -->
                            <p class="product-description">${product.descricao}</p>
                        </div>
                    </a>
                    <div class="product-footer">
                        <!-- Preço do produto -->
                        <div class="price">${priceDisplay}</div>
                        <!-- Botão "Ver Detalhes" que redireciona para a página de detalhes do produto -->
                        <button class="add-to-cart-btn" onclick="window.location.href='/produtos/${product.id}'">
                            <i class="fas fa-eye"></i> Ver Detalhes
                        </button>
                    </div>
                </div>
            `;
            // Adiciona o HTML do card de produto ao grid
            productGrid.innerHTML += productCard;
        });
    }

    // --- Chamada inicial ---
    // Esta linha inicia o processo de busca e renderização dos produtos
    // assim que o DOM (Document Object Model) da página estiver completamente carregado.
    fetchAndRenderBaseProducts();
});
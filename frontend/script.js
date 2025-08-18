// 页面和导航元素
const pages = {
    indexManager: document.getElementById('indexManagerPage'),
    createIndex: document.getElementById('createIndexPage'),
    indexDetail: document.getElementById('indexDetailPage'),
    search: document.getElementById('searchPage')
};

const navButtons = {
    indexManager: document.getElementById('indexManagerBtn'),
    search: document.getElementById('searchBtn')
};

// 当前状态
let currentIndex = null;
let selectedFiles = [];

// 初始化应用
document.addEventListener('DOMContentLoaded', function() {
    // 设置导航按钮事件
    navButtons.indexManager.addEventListener('click', () => showPage('indexManager'));
    navButtons.search.addEventListener('click', () => showPage('search'));
    
    // 设置创建索引页面的事件
    document.getElementById('createIndexBtn').addEventListener('click', () => showPage('createIndex'));
    document.getElementById('backToIndexManager').addEventListener('click', () => showPage('indexManager'));
    document.getElementById('cancelCreateBtn').addEventListener('click', () => showPage('indexManager'));
    document.getElementById('selectFilesBtn').addEventListener('click', handleFileSelect);
    document.getElementById('createIndexForm').addEventListener('submit', createIndex);
    
    // 设置索引详情页面的事件
    document.getElementById('backToIndexList').addEventListener('click', () => showPage('indexManager'));
    document.getElementById('searchInIndexBtn').addEventListener('click', () => showPage('search'));
    
    // 设置搜索页面的事件
    document.getElementById('backToIndexDetail').addEventListener('click', () => showPage('indexDetail'));
    document.getElementById('searchForm').addEventListener('submit', performSearch);
    
    // 初始加载索引列表
    loadIndexList();
    
    // 显示默认页面
    showPage('indexManager');
});

// 页面导航函数
function showPage(pageName) {
    // 隐藏所有页面
    Object.values(pages).forEach(page => {
        page.classList.remove('active');
    });
    
    // 显示请求的页面
    pages[pageName].classList.add('active');
    
    // 更新导航按钮状态
    Object.values(navButtons).forEach(btn => {
        btn.classList.remove('active');
    });
    
    if (pageName === 'indexManager' || pageName === 'createIndex' || pageName === 'indexDetail') {
        navButtons.indexManager.classList.add('active');
    } else if (pageName === 'search') {
        navButtons.search.classList.add('active');
    }
    
    // 根据页面执行特定操作
    if (pageName === 'indexManager') {
        loadIndexList();
    } else if (pageName === 'createIndex') {
        resetCreateIndexForm();
    } else if (pageName === 'indexDetail' && currentIndex) {
        loadIndexDetail(currentIndex);
    } else if (pageName === 'search' && currentIndex) {
        // 可以在这里添加搜索页面的初始化逻辑
    }
}

// 获取状态文本
function getStatusText(status) {
    switch (status) {
        case 'processing': return '处理中';
        case 'completed': return '已完成';
        case 'error': return '错误';
        default: return '未知';
    }
}

// 重置创建索引表单
function resetCreateIndexForm() {
    document.getElementById('indexName').value = '';
    selectedFiles = [];
    updateFileList();
}

// 处理文件选择
async function handleFileSelect(event) {
    const { ipcRenderer } = window.require('electron');
    const filePaths = await ipcRenderer.invoke('open-file-dialog');
    if (filePaths && filePaths.length > 0) {
        // 将文件路径转换为包含name属性的对象
        const newFiles = filePaths.map(path => ({
            path: path,
            name: path.split('/').pop().split('\\').pop() // 提取文件名
        }));
        selectedFiles = [...selectedFiles, ...newFiles];
        updateFileList();
    }
}

// 更新文件列表显示
function updateFileList() {
    const fileListContainer = document.getElementById('fileList');
    
    if (selectedFiles.length === 0) {
        fileListContainer.innerHTML = '<div class="empty-state"><p>未选择任何文件</p></div>';
        return;
    }
    
    fileListContainer.innerHTML = '';
    selectedFiles.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <span>${file.name}</span>
            <button class="remove-file-btn" data-index="${index}">移除</button>
        `;
        fileListContainer.appendChild(fileItem);
    });
    
    // 添加移除按钮事件
    document.querySelectorAll('.remove-file-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const index = parseInt(this.getAttribute('data-index'));
            selectedFiles.splice(index, 1);
            updateFileList();
        });
    });
}

// API 调用函数
const API_BASE = 'http://localhost:5001/api';

async function apiCall(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
        headers: {
            'Content-Type': 'application/json',
        },
        ...options
    };
    
    try {
        const response = await fetch(url, config);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || '请求失败');
        }
        
        return data;
    } catch (error) {
        console.error('API调用失败:', error);
        throw error;
    }
}

// 加载索引列表
async function loadIndexList() {
    try {
        const indexes = await apiCall('/indexes');
        const indexListContainer = document.getElementById('indexList');
        
        if (indexes.length === 0) {
            indexListContainer.innerHTML = '<div class="empty-state"><p>暂无索引数据</p></div>';
            return;
        }
        
        indexListContainer.innerHTML = '';
        indexes.forEach(index => {
            const indexCard = document.createElement('div');
            indexCard.className = 'index-card';
            indexCard.innerHTML = `
                <h3>${index.name}</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <span class="label">创建日期:</span>
                        <span class="value">${index.createDate}</span>
                    </div>
                    <div class="info-item">
                        <span class="label">索引状态:</span>
                        <span class="value status-${index.status}">${getStatusText(index.status)}</span>
                    </div>
                </div>
            `;
            indexCard.addEventListener('click', () => {
                currentIndex = index;
                showPage('indexDetail');
            });
            indexListContainer.appendChild(indexCard);
        });
    } catch (error) {
        console.error('加载索引列表失败:', error);
        document.getElementById('indexList').innerHTML = '<div class="empty-state"><p>加载数据失败</p></div>';
    }
}

// 创建索引
async function createIndex(event) {
    event.preventDefault();
    
    const indexName = document.getElementById('indexName').value.trim();
    
    if (!indexName) {
        alert('请输入索引名称');
        return;
    }
    
    if (selectedFiles.length === 0) {
        alert('请选择至少一个视频文件');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/indexes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: indexName,
                filePaths: selectedFiles.map(file => file.path)
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || '请求失败');
        }
        
        alert(`索引 "${indexName}" 创建成功！`);
        currentIndex = data;
        showPage('indexDetail');
    } catch (error) {
        alert(`创建索引失败: ${error.message}`);
    }
}

// 加载索引详情
async function loadIndexDetail(index) {
    if (!index) return;
    
    try {
        const indexDetail = await apiCall(`/indexes/${index.id}`);
        
        // 更新基本信息
        document.getElementById('detailIndexName').textContent = indexDetail.name;
        document.getElementById('detailCreateDate').textContent = indexDetail.createDate;
        document.getElementById('detailIndexStatus').textContent = getStatusText(indexDetail.status);
        document.getElementById('detailIndexStatus').className = `value status-${indexDetail.status}`;
        
        // 更新视频文件列表
        const videoTableBody = document.getElementById('videoTableBody');
        videoTableBody.innerHTML = '';
        
        // 如果有文件数据，则显示文件列表
        if (indexDetail.files && indexDetail.files.length > 0) {
            indexDetail.files.forEach(file => {
                // 只显示文件名，不显示完整路径
                const fileName = file.path.split('/').pop().split('\\').pop();
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${fileName}</td>
                    <td class="status-${file.status}">${getStatusText(file.status)}</td>
                    <td><button class="btn-secondary view-video-btn" data-path="${file.path}">查看</button></td>
                `;
                videoTableBody.appendChild(row);
            });
            
            // 添加查看按钮事件
            document.querySelectorAll('.view-video-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const filePath = this.getAttribute('data-path');
                    alert(`查看视频文件: ${filePath}\n(在实际应用中会打开视频播放器)`);
                });
            });
        } else {
            // 如果没有文件数据，显示空状态
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="3" class="empty-state">暂无视频文件</td>';
            videoTableBody.appendChild(row);
        }
    } catch (error) {
        console.error('加载索引详情失败:', error);
        document.getElementById('videoTableBody').innerHTML = '<tr><td colspan="3" class="empty-state">加载数据失败</td></tr>';
    }
}

// 执行搜索
async function performSearch(event) {
    event.preventDefault();
    
    const query = document.getElementById('searchQuery').value.trim();
    
    if (!query) {
        alert('请输入搜索关键词');
        return;
    }
    
    if (!currentIndex) {
        alert('请先选择一个索引');
        return;
    }
    
    try {
        const results = await apiCall(`/indexes/${currentIndex.id}/search`, {
            method: 'POST',
            body: JSON.stringify({ query })
        });
        
        displaySearchResults(results);
    } catch (error) {
        alert(`搜索失败: ${error.message}`);
    }
}

// 显示搜索结果
function displaySearchResults(results) {
    const resultsBody = document.getElementById('searchResultsBody');
    const noResults = document.getElementById('noResults');
    
    if (results.length === 0) {
        resultsBody.innerHTML = '';
        noResults.style.display = 'block';
        return;
    }
    
    noResults.style.display = 'none';
    resultsBody.innerHTML = '';
    
    results.forEach(result => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${result.videoPath}</td>
            <td>${result.startTime}</td>
            <td>${result.text}</td>
        `;
        resultsBody.appendChild(row);
    });
}

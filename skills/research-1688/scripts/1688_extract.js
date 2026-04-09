// 1688商品ページから構造化データを抽出（AliPrice TXT の補完用）
// AliPrice TXT で取得済みの項目（タイトル・価格・年間販売数・工場基本情報）は除外し、
// TXTでは取れないデータのみを抽出する。
// 用途: agent-browser の eval --stdin で実行
// 出力: JSON文字列

(function() {
  const result = {
    url: location.href,
    product_id: (location.href.match(/offer\/(\d+)/) || [])[1] || '',

    // --- AliPrice TXT にない項目（補完対象）---
    // 価格レンジ（TXTは最低価格のみ）
    price_min: null,
    price_max: null,

    // 产品参数（商品属性）
    product_attrs: {},

    // SKU バリエーション詳細
    sku_dimensions: [],
    sku_images: [],

    // 工場追加情報（TXTには工場名・URLのみ）
    factory_extra: {},

    // OEM/ODM 指標
    oem_indicators: [],

    // 認証・規格
    certifications: [],

    // 详情テキスト
    description_text: '',

    // 商品画像URL
    images: []
  };

  // === 価格レンジ（price_min / price_max）===
  const skuPrices = [];
  document.querySelectorAll('.item-price-stock').forEach(el => {
    const m = el.innerText.match(/([\d.]+)/);
    if (m) skuPrices.push(parseFloat(m[1]));
  });
  if (skuPrices.length > 0) {
    result.price_min = Math.min(...skuPrices);
    result.price_max = Math.max(...skuPrices);
  } else {
    // フォールバック: メイン価格
    const mainPrice = document.querySelector('.price-info, .price-comp');
    if (mainPrice) {
      const m = mainPrice.innerText.match(/([\d.]+)/);
      if (m) result.price_min = result.price_max = parseFloat(m[1]);
    }
  }

  // === 产品参数（商品属性）===
  const attrEl = document.querySelector('.module-od-product-attributes');
  if (attrEl) {
    const text = attrEl.innerText;
    const lines = text.split('\n').map(l => l.trim()).filter(l => l);
    for (let i = 0; i < lines.length - 1; i++) {
      const key = lines[i];
      const val = lines[i + 1];
      if (key && val && key.length < 30 && !val.includes('\t') && val !== key) {
        result.product_attrs[key] = val;
        i++; // skip value line
      }
    }
  }
  // タブ区切りフォールバック
  if (Object.keys(result.product_attrs).length === 0 && attrEl) {
    attrEl.innerText.split('\n').forEach(line => {
      const parts = line.split('\t').map(s => s.trim()).filter(s => s);
      for (let i = 0; i < parts.length - 1; i += 2) {
        if (parts[i].length < 30 && parts[i+1]) {
          result.product_attrs[parts[i]] = parts[i+1];
        }
      }
    });
  }

  // === SKU バリエーション ===
  const skuContainer = document.querySelector('[class*="sku"]');
  if (skuContainer) {
    const headings = skuContainer.querySelectorAll('h3');
    headings.forEach(h => {
      const dimName = (h.textContent || '').trim();
      if (!dimName || dimName.length > 20) return;
      const dim = { name: dimName, options: [] };
      // h3の親または次の兄弟から選択肢を収集
      const parent = h.closest('div') || h.parentElement;
      if (parent) {
        parent.querySelectorAll('[title]').forEach(item => {
          const name = (item.getAttribute('title') || '').trim();
          if (name && name.length < 80 && !name.startsWith('¥') && !/^\d+\.\d+$/.test(name)) {
            dim.options.push(name);
          }
        });
      }
      // フォールバック: 次の兄弟を探索
      if (dim.options.length === 0) {
        let next = h.nextElementSibling;
        while (next && next.tagName !== 'H3') {
          next.querySelectorAll('[title], [class*="item-name"]').forEach(item => {
            const name = (item.getAttribute('title') || item.textContent || '').trim();
            if (name && name.length < 80 && !name.startsWith('¥')) {
              dim.options.push(name);
            }
          });
          next = next.nextElementSibling;
        }
      }
      // 重複除去
      dim.options = [...new Set(dim.options)];
      if (dim.options.length > 0) result.sku_dimensions.push(dim);
    });

    // SKU画像URL
    skuContainer.querySelectorAll('img[src*="alicdn.com"]').forEach(img => {
      const src = (img.src || '').split('?')[0].replace(/_sum\.jpg$/, '.jpg');
      if (src && !result.sku_images.includes(src)) result.sku_images.push(src);
    });
  }

  // === 工場追加情報 ===
  const shopInfo = document.querySelector('.od-shop-navigation, [class*="shop-info"], [class*="winport"]');
  if (shopInfo) {
    const text = shopInfo.textContent || '';
    const yearMatch = text.match(/入驻(\d+)年/);
    if (yearMatch) result.factory_extra.years = parseInt(yearMatch[1]);
    const mainMatch = text.match(/主营[：:]\s*(.+)/);
    if (mainMatch) result.factory_extra.main_products = mainMatch[1].trim();
    const rateMatch = text.match(/回头率\s*([\d.]+)%/);
    if (rateMatch) result.factory_extra.repeat_rate = rateMatch[1] + '%';
    const scoreMatch = text.match(/服务[分數]\s*([\d.]+)/);
    if (scoreMatch) result.factory_extra.service_score = scoreMatch[1];
    const shipMatch = text.match(/准时发货率\s*([\d.]+)%/);
    if (shipMatch) result.factory_extra.ontime_rate = shipMatch[1] + '%';
    const reviewMatch = text.match(/好评率\s*([\d.]+)%/);
    if (reviewMatch) result.factory_extra.good_review_rate = reviewMatch[1] + '%';
  }

  // === OEM/ODM 指標 ===
  const bodyText = document.body.innerText;
  ['加工定制', '贴牌', 'OEM', 'ODM', '定做', '来样', '来图', '打样',
   'プライベートブランド', 'ライセンス取得可能'].forEach(kw => {
    if (bodyText.includes(kw)) result.oem_indicators.push(kw);
  });

  // === 認証・規格 ===
  ['CE', 'FDA', 'SGS', 'ISO', 'BSCI', 'REACH', 'ROHS', 'CCC',
   'カテゴリーA', 'カテゴリA', 'A类', 'GB'].forEach(kw => {
    if (bodyText.includes(kw)) result.certifications.push(kw);
  });

  // === 详情テキスト ===
  const descEl = document.querySelector('.module-od-product-attributes');
  if (descEl) {
    result.description_text = descEl.innerText.trim().substring(0, 3000);
  }

  // === 商品画像URL ===
  const seenImgs = new Set();
  document.querySelectorAll('.detail-gallery img, [class*="gallery"] img, .tab-pane img').forEach(img => {
    const src = (img.src || img.getAttribute('data-src') || '').split('?')[0];
    if (src && src.includes('alicdn.com') && !seenImgs.has(src)) {
      seenImgs.add(src);
      result.images.push(src);
    }
  });

  return JSON.stringify(result);
})();

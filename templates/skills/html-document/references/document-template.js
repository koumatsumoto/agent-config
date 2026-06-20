// km:html-document の図操作スクリプト。document-template.html の末尾 <script> にビルドで挿入して単一ファイルにする。

// Mermaid 初期化。htmlLabels:false で図ラベルを <foreignObject>（HTML）ではなく SVG <text> で描く。
// foreignObject 入り SVG は canvas 描画時に汚染され toBlob が失敗するため、PNG/WebP 化を成立させるのに必須。
mermaid.initialize({ startOnLoad: true, securityLevel: 'strict', htmlLabels: false, flowchart: { htmlLabels: false } });

// 図の操作（完全クライアント側・外部送信なし）。各 figure.diagram に付与する:
// - マウスホイールで拡大 / 縮小、ドラッグで移動、ダブルクリックでリセット
// - WebP ボタンで SVG を canvas 経由のラスタ画像にして別タブで開く（ポップアップ抑止時はダウンロード）
// mermaid は load 時に非同期描画するため、ハンドラは figure に張り SVG はイベント時に都度取得する（描画タイミングに依存しない）。
(() => {
  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

  // SVG を指定 MIME のラスタ画像にして別タブで開く。img-src blob: で blob を許可している
  const openAsImage = (svg, mime, ext) => {
    const box = svg.viewBox && svg.viewBox.baseVal;
    const rect = svg.getBoundingClientRect();
    const w = Math.max(1, Math.round((box && box.width) || rect.width));
    const h = Math.max(1, Math.round((box && box.height) || rect.height));
    const clone = svg.cloneNode(true);
    clone.setAttribute('width', w);
    clone.setAttribute('height', h);
    clone.style.transform = 'none'; // 画面表示用の拡縮を画像へ持ち込まない
    const xml = new XMLSerializer().serializeToString(clone);
    const svgUrl = URL.createObjectURL(new Blob([xml], { type: 'image/svg+xml;charset=utf-8' }));
    const img = new Image();
    img.onload = () => {
      const scale = 2; // 高解像度化
      const canvas = document.createElement('canvas');
      canvas.width = w * scale;
      canvas.height = h * scale;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(svgUrl);
      canvas.toBlob((blob) => {
        if (!blob) return;
        const url = URL.createObjectURL(blob);
        const win = window.open(url, '_blank');
        if (!win) { // ポップアップブロック時はダウンロードにフォールバック
          const a = document.createElement('a');
          a.href = url;
          a.download = 'diagram.' + ext;
          a.click();
        }
      }, mime);
    };
    img.src = svgUrl;
  };

  const enhance = (fig) => {
    if (fig.dataset.enhanced) return;
    fig.dataset.enhanced = '1';
    const view = { scale: 1, x: 0, y: 0 };
    const apply = () => {
      const svg = fig.querySelector('svg');
      if (svg) svg.style.transform = `translate(${view.x}px, ${view.y}px) scale(${view.scale})`;
    };
    const reset = () => { view.scale = 1; view.x = 0; view.y = 0; apply(); };

    fig.addEventListener('wheel', (e) => {
      e.preventDefault();
      view.scale = clamp(view.scale * (e.deltaY < 0 ? 1.1 : 1 / 1.1), 0.2, 8);
      apply();
    }, { passive: false });

    let drag = null;
    fig.addEventListener('pointerdown', (e) => {
      if (e.target.closest('.diagram-tools')) return;
      // 図ラベル・キャプションのテキスト上では選択を優先し pan しない。余白・ノード・エッジ上だけ pan する
      if (e.target.closest('text, tspan, foreignObject, figcaption')) return;
      e.preventDefault(); // 余白からのドラッグでテキスト選択が始まるのを抑止する
      drag = { x: e.clientX - view.x, y: e.clientY - view.y };
      try { fig.setPointerCapture(e.pointerId); } catch (_) { /* 非アクティブな pointer は無視 */ }
      fig.classList.add('grabbing');
    });
    fig.addEventListener('pointermove', (e) => {
      if (!drag) return;
      view.x = e.clientX - drag.x;
      view.y = e.clientY - drag.y;
      apply();
    });
    const endDrag = () => { drag = null; fig.classList.remove('grabbing'); };
    fig.addEventListener('pointerup', endDrag);
    fig.addEventListener('pointercancel', endDrag);
    fig.addEventListener('dblclick', reset);

    const tools = document.createElement('div');
    tools.className = 'diagram-tools';
    const addButton = (label, onClick) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = label;
      button.addEventListener('click', onClick);
      tools.appendChild(button);
    };
    const withSvg = (fn) => () => { const svg = fig.querySelector('svg'); if (svg) fn(svg); };
    addButton('WebP', withSvg((svg) => openAsImage(svg, 'image/webp', 'webp')));
    addButton('リセット', reset);
    fig.appendChild(tools);
  };

  // mermaid の描画完了は待たない: figure は静的に存在するので load 時にハンドラを張る
  window.addEventListener('load', () => {
    document.querySelectorAll('figure.diagram').forEach(enhance);
  });
})();

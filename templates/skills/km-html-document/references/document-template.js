// km-html-document の図操作スクリプト。document-template.html の末尾 <script> にビルドで挿入して単一ファイルにする。

// Mermaid 初期化。htmlLabels:false で図ラベルを <foreignObject>（HTML）ではなく SVG <text> で描く。
// foreignObject 入り SVG は canvas 描画時に汚染され toBlob が失敗するため、WebP 化を成立させるのに必須。
mermaid.initialize({ startOnLoad: true, securityLevel: 'strict', htmlLabels: false, flowchart: { htmlLabels: false } });

// 図の操作（クライアント内で完結し、外部送信なし）。各figure.diagramに次の操作を付与する:
// - Ctrl+ホイールまたは＋ / −ボタンで拡大・縮小する
// - ドラッグで移動し、ダブルクリックまたはリセットボタンで初期化する
// - WebPボタンでSVGをラスタ画像に変換して別タブで開く。ポップアップが抑止された場合はダウンロードする
// mermaidは読み込み時に非同期描画するため、ハンドラはfigureに張り、SVGはイベント時に都度取得する（描画タイミングに依存しない）。
(() => {
  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

  // SVGを指定MIMEのラスタ画像にして別タブで開く。img-srcのblob:でBlob URLを許可している
  const openAsImage = (svg, mime, ext) => {
    const box = svg.viewBox && svg.viewBox.baseVal;
    const rect = svg.getBoundingClientRect();
    const w = Math.max(1, Math.round((box && box.width) || rect.width));
    const h = Math.max(1, Math.round((box && box.height) || rect.height));
    const clone = svg.cloneNode(true);
    clone.setAttribute('width', w);
    clone.setAttribute('height', h);
    // 画面表示用の拡大縮小と移動（要素内のwidth/height/maxWidth/transform）を画像へ持ち込まない
    clone.style.width = '';
    clone.style.height = '';
    clone.style.maxWidth = '';
    clone.style.transform = 'none';
    const xml = new XMLSerializer().serializeToString(clone);
    const svgUrl = URL.createObjectURL(new Blob([xml], { type: 'image/svg+xml;charset=utf-8' }));
    const img = new Image();
    img.onload = () => {
      try {
        const scale = 2; // 高解像度化
        const canvas = document.createElement('canvas');
        canvas.width = w * scale;
        canvas.height = h * scale;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        canvas.toBlob((blob) => {
          if (!blob) { console.error('図の書き出し: toBlobがnull（canvas上限超過または形式未対応の可能性）'); return; }
          const url = URL.createObjectURL(blob);
          const win = window.open(url, '_blank');
          if (!win) { // ポップアップブロック時はダウンロードにフォールバック
            const a = document.createElement('a');
            a.href = url;
            a.download = 'diagram.' + ext;
            a.click();
          }
        }, mime);
      } catch (err) {
        console.error('図の書き出しに失敗', err); // 例: foreignObjectなどでcanvasが汚染された場合
      } finally {
        URL.revokeObjectURL(svgUrl);
      }
    };
    img.onerror = () => { URL.revokeObjectURL(svgUrl); console.error('図の書き出し用SVGを読み込めませんでした'); };
    img.src = svgUrl;
  };

  const enhance = (fig) => {
    if (fig.dataset.enhanced) return;
    fig.dataset.enhanced = '1';
    const view = { scale: 1, x: 0, y: 0 };
    let base = null; // scale=1 の自然サイズ（初回 apply で記録）
    const apply = () => {
      const svg = fig.querySelector('svg');
      if (!svg) return;
      if (!base) {
        const r = svg.getBoundingClientRect();
        if (r.width < 1) return; // まだ描画されていない
        base = { w: r.width, h: r.height };
        svg.style.maxWidth = 'none'; // 拡大時に mermaid の max-width で頭打ちさせない
      }
      // ズームは表示サイズ（width/height）で行う → SVG ベクタが解像度に追従し、文字が拡大してもぼけない
      svg.style.width = (base.w * view.scale) + 'px';
      svg.style.height = (base.h * view.scale) + 'px';
      // パンは translate（リサンプルされないので鮮明なまま）
      svg.style.transform = `translate(${view.x}px, ${view.y}px)`;
    };
    const reset = () => { view.scale = 1; view.x = 0; view.y = 0; apply(); };
    const zoomBy = (factor) => { view.scale = clamp(view.scale * factor, 0.2, 8); apply(); };

    // 拡縮は Ctrl+ホイールに限定する。素のホイールはページスクロールに通し、図の上でもスクロールを妨げない
    fig.addEventListener('wheel', (e) => {
      if (!e.ctrlKey) return; // 素のホイールはページスクロールに任せる
      e.preventDefault(); // ブラウザのページ全体ズームを抑止し、図だけを拡縮する
      view.scale = clamp(view.scale * (e.deltaY < 0 ? 1.1 : 1 / 1.1), 0.2, 8);
      apply();
    }, { passive: false });

    let drag = null;
    fig.addEventListener('pointerdown', (e) => {
      if (e.button !== 0) return; // 主ボタンのみ（右・中クリックで移動を始めない）
      if (e.target.closest('.diagram-tools')) return;
      // 図ラベルとキャプションのテキスト上では選択を優先し、移動しない。余白、ノード、エッジ上だけ移動する
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
    window.addEventListener('pointerup', endDrag); // captureに失敗しても、図の外で離せば移動を終える
    fig.addEventListener('dblclick', reset);

    // 印刷時はズーム/パンを一時解除して自然サイズで刷り、印刷後に画面の表示を復元する
    let savedView = null;
    window.addEventListener('beforeprint', () => {
      if (!base) return; // 未操作の図は mermaid の自然描画のまま
      savedView = { ...view };
      view.scale = 1; view.x = 0; view.y = 0; apply();
    });
    window.addEventListener('afterprint', () => {
      if (!savedView) return;
      Object.assign(view, savedView);
      savedView = null;
      apply();
    });

    const tools = document.createElement('div');
    tools.className = 'diagram-tools';
    const addButton = (label, onClick, title) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = label;
      if (title) button.title = title;
      button.addEventListener('click', onClick);
      tools.appendChild(button);
    };
    const withSvg = (fn) => () => { const svg = fig.querySelector('svg'); if (svg) fn(svg); };
    const zoomStep = 1.2;
    addButton('−', () => zoomBy(1 / zoomStep), '縮小');
    addButton('＋', () => zoomBy(zoomStep), '拡大');
    addButton('リセット', reset);
    addButton('WebP', withSvg((svg) => openAsImage(svg, 'image/webp', 'webp')));
    fig.appendChild(tools);
  };

  // mermaidの描画完了は待たない。figureは静的に存在するため、読み込み時にハンドラを張る
  window.addEventListener('load', () => {
    document.querySelectorAll('figure.diagram').forEach(enhance);
  });
})();

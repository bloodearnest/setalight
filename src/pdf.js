import { h } from 'preact'
import { useState, useEffect, useRef, useMemo, useCallback } from 'preact/hooks'
import PdfJsLib from '@bundled-es-modules/pdfjs-dist/build/pdf'
import { useEventListener } from './hooks'

const WORKER_SRC = 'pdf.worker.js'
PdfJsLib.GlobalWorkerOptions.workerSrc = WORKER_SRC

const Pdf = ({ data, onDocumentComplete, page, scale }) => {
  const containerRef = useRef(null)
  const [, numPages] = usePdf({ containerRef, data, page, scale })

  useEffect(() => {
    onDocumentComplete(numPages)
  }, [numPages])

  return <div ref={containerRef} />
}

Pdf.defaultProps = {
  onDocumentComplete: () => {}
}

export const usePdf = ({ containerRef, data, page = 1, scale = 1 }) => {
  const [pdf, setPdf] = useState()
  const [width, setWidth] = useState(window.innerWidth)

  useEffect(() => {
    const config = { data: data }
    PdfJsLib.getDocument(config).promise.then(setPdf)
  }, [data])

  // handle changes
  useEffect(() => {
    if (pdf) {
      pdf.getPage(page).then((p) => drawPDF(p))
    }
  }, [pdf, page, width, scale, containerRef])

  useEventListener('resize', e => setWidth(window.innerWidth))

  // draw a page of the pdf
  const drawPDF = (page) => {
    const pageWidth = page.getViewport({ scale: 1.0 }).width
    const base_scale = width / pageWidth
    const viewport = page.getViewport({ scale: base_scale * scale })
    const canvas = document.createElement('canvas')
    const canvasContext = canvas.getContext('2d')
    canvas.height = viewport.height
    canvas.width = viewport.width
    const renderContext = {
      canvasContext,
      viewport
    }
    page.render(renderContext).promise.then(() => {
      while (containerRef.current.firstChild) {
        containerRef.current.firstChild.remove()
      }
      containerRef.current.appendChild(canvas)
    })
  }

  const loading = useMemo(() => !pdf, [pdf])
  const numPages = useMemo(() => (pdf ? pdf._pdfInfo.numPages : null), [pdf])

  return [loading, numPages]
}

export default Pdf

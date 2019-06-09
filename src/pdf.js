import { h } from 'preact'
import { useState, useEffect, useRef, useMemo } from 'preact/hooks'
import PdfJsLib from '@bundled-es-modules/pdfjs-dist/build/pdf'

const WORKER_SRC = 'pdf.worker.js'
PdfJsLib.GlobalWorkerOptions.workerSrc = WORKER_SRC

const Pdf = ({ file, onDocumentComplete, page, scale }) => {
  const containerRef = useRef(null)
  const [, numPages] = usePdf({ containerRef, file, page, scale })

  useEffect(() => {
    onDocumentComplete(numPages)
  }, [numPages])

  return <div ref={containerRef} />
}

Pdf.defaultProps = {
  onDocumentComplete: () => {}
}

export const usePdf = ({ containerRef, file, page = 1, scale = 1 }) => {
  const [pdf, setPdf] = useState()

  useEffect(() => {
    const config = { url: file }
    PdfJsLib.getDocument(config).promise.then(setPdf)
  }, [file])

  // handle changes
  useEffect(() => {
    if (pdf) {
      pdf.getPage(page).then((p) => drawPDF(p))
    }
  }, [pdf, page, scale, containerRef])

  // draw a page of the pdf
  const drawPDF = (page) => {
    const pageWidth = page.getViewport({ scale: 1.0 }).width
    const base_scale = (screen.width / pageWidth)
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

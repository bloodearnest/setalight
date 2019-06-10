import { h, render, Fragment } from 'preact'
import { useState, useCallback } from 'preact/hooks'
import { tokenise, TOKENS } from './chordpro'
import { map, copy, scrollToInternal, toggleFullScreen, toggleWakeLock } from './platform'
import { transposeChord, calculateTranspose, NOTES_ALL } from './music'
import Pdf from './pdf'



// the main application component
function SetList ({ setlist, }) {
  const [order, setOrder] = useState(setlist.order)
  const setNewOrder = useCallback(o => setOrder(o), [order, setOrder])
  return (
    <Fragment>
      <Page><Index setlist={setlist} order={order} setOrder={setNewOrder} /></Page>
      {order.map((id) => <Page><Song key={id} song={setlist.songs[id]} /></Page>) }
    </Fragment>
  )
}

function Page( {children} ) {
  return (
    <div class="page-container"><div class="page">{children}</div></div>
  )
}

function FakeInternalLink ({ text, target, children }) {
  // this avoids actuall setting window.location.hash, which I think we want
  // also, it avoids the default link drag behaviour
  const go = e => scrollToInternal(target)
  return <span class='link' onclick={go} ontouchstart={go}>{text}{children}</span>
}

function Index ({ setlist, order, setOrder }) {
  // this does a crude DOM-based Drag and Drop list reordering
  // there's other way to get info that's also available in dragenter to the song being dragged :(
  let draggedSongId = null

  const dragStart = e => {
    e.target.classList.add('dragging')
    draggedSongId = e.target.getAttribute('data-id')
    e.dataTransfer.effectAllowed = 'move'
  }
  const dragOver = e => {
    if (e.preventDefault) e.preventDefault() // Necessary. Allows us to drop.
    e.dataTransfer.dropEffect = 'move'
    return false
  }

  const dragEnter = e => {
    if (e.target.closest('.song-index').getAttribute('data-id') !== draggedSongId) {
      e.target.classList.add('over')
    }
  }
  const dragLeave = e => e.target.classList.remove('over')
  const dragEnd = e => e.target.classList.remove('dragging')

  const drop = e => {
    // e.target is the drop target
    if (e.stopPropagation) e.stopPropagation() // stops the browser from redirecting.

    let node = e.target.closest('.song-index')
    const thisSongId = node.getAttribute('data-id')
    const targetIndex = parseInt(node.getAttribute('data-index'))

    if (draggedSongId === thisSongId) {
      return false
    }

    let newOrder = []
    for (let index = 0; index < order.length; index += 1) {
      const id = order[index]
      if (id === draggedSongId) {
        continue
      }
      newOrder.push(id)
      if (index === targetIndex) {
        newOrder.push(draggedSongId)
      }
    }
    setOrder(newOrder)
    draggedSongId = null
    return false
  }

  let messages = []

  if (setlist.html) {
    for (const msg of setlist.html) {
      messages.push(<section dangerouslySetInnerHTML={{__html: msg}}/>)
    }
  }
  else if (setlist.text) {
    for (const msg of setlist.text) {
      messages.push(<pre>{msg}</pre>)
    }
  }

  function toggleSetlist (ev) {
    toggleFullScreen()
    toggleWakeLock()
  }

  return (
    <article class='index' id='index'>
      <header class="title">{ setlist.title }
        <span class='fullscreen' onclick={toggleSetlist} ontouchstart={toggleSetlist}><i class='icon-resize-full' /></span>
      </header>
      <table class='songlist'>
        {order.map((id, index) => {
          const song = setlist.songs[id]
          return (
            <tr>
              <td key={'index-' + id}
                class='song-index'
                data-id={id}
                data-index={index}
                draggable
                ondragstart={dragStart}
                ondragover={dragOver}
                ondragenter={dragEnter}
                ondragleave={dragLeave}
                ondragend={dragEnd}
                ondrop={drop}
              >
                <i class='icon-menu' /> <FakeInternalLink text={song.title} target={song.id} />
              </td>
              <td>{ song.key || '?'}</td>
              <td>{ song.time }</td>
              <td>{ song.tempo }</td>
            </tr>
          )
        })}
      </table>
      {messages}
    </article>
  )
}

function PdfSheet ({ data }) {
  const [zoom, setZoom] = useState(1.0)

  const zoomCallback = useCallback(e => {
    e.preventDefault()
    const newZoom = zoom + (e.deltaY * 0.001)
    setZoom(Math.min(Math.max(0.5, newZoom), 3))
  }, [zoom, setZoom])

  return (
    <div class='pdfcontainer' onwheel={zoomCallback}>
      <Pdf data={data} scale={zoom} />
    </div>
  )
}

function Song ({ song }) {
  const [transposedKey, setTransposedKey] = useState(song.key)
  var transposeMap = null
  if (song.key && transposedKey != song.key) {
    transposeMap = calculateTranspose(song.key, transposedKey)
  }
  if (song.type === 'pdf-failed') {
    return (
      <article class='pdf' id={song.id}>
        <SongTitle song={song} transposedKey={transposedKey} setKey={setTransposedKey} showInfo={false}/>
        <PdfSheet data={PDFDATA[song.id]} />
      </article>
    )
  }
  return (
    <article class='song' id={song.id}>
      <SongTitle song={song} transposedKey={transposedKey} setKey={setTransposedKey} />
      {map(song.sections, (name, section) => <Section name={name} section={section} transposeMap={transposeMap} />)}
    </article>
  )
}

function SongTitle ({ song, transposedKey, setKey, showInfo }) {
  let key = transposedKey || song.key || ''
  let nodes = []
  if (showInfo === undefined || showInfo) {
    if (song['key']) {
      nodes.push(
        <select class='key' value={key} onChange={ev => setKey(ev.target.value)}>
          {NOTES_ALL.map(n => <option >{n}</option>)}
        </select>
      )
      nodes.push(' | ')
    }
    if (song.capo) {
      nodes.push('Capo ' + song.capo)
      nodes.push(' | ')
    }
    if (song.time) {
      nodes.push(song.time)
      nodes.push(' | ')
    }
    if (song.tempo) {
      nodes.push(song.tempo)
      nodes.push(' | ')
    }
  }
  nodes.push(<FakeInternalLink target='index'><i class='icon-home' /></FakeInternalLink>)

  return (
    <header class='title'>{ song['title'] }
      <span class='info'>{nodes}</span>
    </header>
  )
}

function Section ({ name, section, transposeMap }) {
  const [collapsed, setCollapsed] = useState(false)
  const [chords, setChords] = useState(true)
  const lines = section.split(/\n/)
  const toggleCollapsed = e => {
    e.preventDefault()
    setCollapsed(!collapsed)
  }
  const toggleChords = e => {
    e.preventDefault()
    setChords(!chords)
  }
  const _class = (collapsed ? 'collapsed ' : ' ') + (chords ? ' ' : 'hide-chords')
  return (
    <section className={_class}>
      <header>
        <span class='name toggle' onclick={toggleCollapsed} ontouchstart={toggleCollapsed}>{name}</span>
        <span class='collapse toggle' onclick={toggleCollapsed} ontouchstart={toggleCollapsed}> <i class='icon-angle-up' /></span>
        <span class='expand toggle' onclick={toggleCollapsed} ontouchstart={toggleCollapsed}> <i class='icon-angle-down' /></span>
        &nbsp;<span class='show-chords toggle' onclick={toggleChords} ontouchstart={toggleChords}>A♭</span>
      </header>
      {lines.map((l) => <Line line={l} transposeMap={transposeMap} />)}
    </section>
  )
}

const TOKEN_CLASS = {}
TOKEN_CLASS[TOKENS.CHORD] = 'chord'
TOKEN_CLASS[TOKENS.COMMENT] = 'comment'
TOKEN_CLASS[TOKENS.SPACE] = 'space'
TOKEN_CLASS[TOKENS.HYPHEN] = 'hyphen'

const RAISED_TOKENS = [TOKENS.CHORD, TOKENS.COMMENT]

function Line ({ line, transposeMap }) {
  // split on [chords] or {directives}, removing undefineds
  var nodes = []
  const [line_type, tokens] = tokenise(line)

  for (var i = 0; i < tokens.length; i += 1) {
    const [current, next] = tokens[i]
    var className = TOKEN_CLASS[current.type]

    switch (current.type) {
      case TOKENS.CHORD:
      case TOKENS.COMMENT:
        var wrapperClass = 'chordlyric '
        var lyric = ' '
        var value = current.value
        // is the next token not a chord/comment?
        if (next && !RAISED_TOKENS.includes(next.type)) {
          if (next.type === TOKENS.SPACE || next.value[0] === '-' || next.value[1] === '-') {
            wrapperClass += 'spaced-chord'
          }
          // pull the next lyric into this node
          lyric = next.value
          i += 1
        }
        if (transposeMap && current.type === TOKENS.CHORD && value !== '|') {
          value = transposeChord(value, transposeMap)
        }
        if (line_type === 'both') {
          nodes.push(
            <span className={wrapperClass}>
              <span className={className}>{value}</span>
              <span class='lyric'>{lyric}</span>
            </span>
          )
        } else {
          nodes.push(
            <span className={className}>{value}</span>
          )
        }
        break

      case TOKENS.HYPHEN:
      case TOKENS.SPACE:
        nodes.push(<span className={className}>{current.value}</span>)
        break

      case TOKENS.LYRIC:
        nodes.push(current.value)
        break

      default:
        console.error('Unknown token type: ', current)
        break
    }
  }
  return <p className={'line ' + line_type}>{nodes}</p>
}

function SetAlight (original_setlist, element) {
  let setlist = copy(original_setlist)
  console.log(setlist)
  render(<SetList setlist={setlist}/>, element)
}

const SETLIST = JSON.parse(document.getElementById('setlist').innerHTML)
const PDFDATA = JSON.parse(document.getElementById('pdfdata').innerHTML)
for (const id of Object.keys(PDFDATA)) {
  PDFDATA[id] = window.atob(PDFDATA[id])
}

const app = document.getElementById('app')
SetAlight(SETLIST, app)

import { useLayoutEffect } from 'react';
import Lenis from 'lenis';
import { animate, createScope, stagger } from 'animejs';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

// Lenis owns scrolling, GSAP owns chapter movement, Anime owns entrances/clicks.
// A shared GSAP clock keeps scrolling and ScrollTrigger synchronized.
export function useWebsiteMotion(root) {
  useLayoutEffect(() => {
    const media = gsap.matchMedia();
    media.add('(prefers-reduced-motion: no-preference)', () => {
      const lenis = new Lenis({
        lerp: 0.085,
        smoothWheel: true,
        syncTouch: false,
        anchors: true,
        prevent: node => !!node.closest?.('.workflow-rail, pre'),
      });
      const tick = seconds => lenis.raf(seconds * 1000);
      lenis.on('scroll', ScrollTrigger.update);
      gsap.ticker.add(tick);

      const chapters = gsap.context(() => {
        gsap.utils.toArray('[data-reveal]').forEach(element => {
          gsap.fromTo(element, { y: 24 }, {
            y: -12, ease: 'none',
            scrollTrigger: { trigger: element, start: 'top 95%', end: 'bottom 15%', scrub: 1 },
          });
        });
      }, root);

      const entrances = createScope({ root: root.current }).add(() => {
        animate('.hero h1', { translateY: [24, 0], duration: 900, ease: 'outExpo' });
        animate('.hero-graph .graph-node', {
          opacity: [0, 1],
          duration: 650, delay: stagger(100, { start: 180 }), ease: 'outCubic',
        });
      });
      const feedback = createScope({ root: root.current });
      const click = event => {
        const control = event.target.closest('button, a.button');
        if (!control || !root.current.contains(control)) return;
        feedback.add(() => animate(control, { scale: [0.97, 1], duration: 220, ease: 'outQuad' }));
      };
      const element = root.current;
      element.addEventListener('click', click);

      return () => {
        element.removeEventListener('click', click);
        feedback.revert();
        entrances.revert();
        chapters.revert();
        gsap.ticker.remove(tick);
        lenis.off('scroll', ScrollTrigger.update);
        lenis.destroy();
      };
    });
    return () => media.revert();
  }, [root]);
}
